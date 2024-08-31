import dotenv from 'dotenv';
import express from 'express';
import { engine } from 'express-handlebars';
import axios from 'axios';
import multer from 'multer';
import oci from 'oci-sdk';
import path from 'path';
import fs from 'fs';

// [Node.js]
const app = express();
const upload = multer({ dest: 'uploads/' });
dotenv.config();

// [OCI Config]
const provider      = new oci.common.ConfigFileAuthenticationDetailsProvider("./oci/config", "DEFAULT");
const signer        = new oci.common.DefaultRequestSigner(provider);

// [OCI Object Storage]
const client        = new oci.objectstorage.ObjectStorageClient({authenticationDetailsProvider: provider});
const bucketName    = process.env.OBJ_BUCKETNAME;
const namespaceName = process.env.OBJ_NAMESPACENAME;

// [OCI Data Science]: Endpoint 
const modelEndpoint = process.env.DATASCIENCE_MODEL_ENDPOINT;

// [OCI OpenSearch]: Parameters
const apiEndpoint   = process.env.OPENSEARCH_APIENDPOINT;
const username      = process.env.OPENSEARCH_USERNAME;
const password      = process.env.OPENSEARCH_PASSWORD;
const searchIndex   = process.env.OPENSEARCH_SEARCHINDEX;
const opensearch    = `${apiEndpoint}/${searchIndex}/_search`;

// [Helper: search.hbs]: Truncate Text
const truncate = (text, length) => {
  if (text.length > length) {
      return text.slice(0, length) + '...';
  }
  return text;
};

// [Helper: search.hbs]: Highlight Text
const highlight = (content, search) => {  
  if (!search) return content;
  const regex = new RegExp(`(${search})`, 'gi');
  return content.replace(regex, '<span class="highlight">$1</span>');
};

// [Handlebars][helper]
app.engine('hbs', engine({
  defaultLayout: 'main',
  extname: '.hbs',
  helpers: {
      truncate: truncate,
      highlight: highlight,
      eq: (a, b) => a === b
  }
}));
app.set('view engine', 'hbs');
app.set('views', './views');

// [Middleware:Express] Load static files from the 'public' folder
app.use(express.static('public'));

// [Middleware:Express] Parse JSON bodies
app.use(express.json());

// [Middleware:Express] Parsing URL-encoded request bodies
app.use(express.urlencoded({ extended: true }));

// [Var] Chat json variable in memory
let jsonChat = [];

// Defines routes for rendering views, handling forms, and processing data.
app.get("/",        (req, res) => { res.render("index") })

app.get("/upload",  (req, res) => { res.render("upload") });
app.post('/upload', upload.single('file'), async (req, res) => { await fn_upload(req, res); });

app.get("/search",  (req, res) => { fn_search(req, res) });
app.post("/search", (req, res) => { fn_search(req, res) });

app.get("/chat",    (req, res) => { fn_files(req, res, jsonChat) });
app.post("/chat",   (req, res) => { fn_chat(req, res) });
app.post('/reset',  (req, res) => { jsonChat = []; res.redirect('/chat'); });

/**
 * Uploads a file to OCI Object Storage and renders the response.
 * 
 * @param {Object} req - Express request object.
 * @param {Object} res - Express response object.
 */
async function fn_upload(req, res) {
  //Constants
  const file = req.file;
  if (!file) return res.status(400).send('No file uploaded...');  
  const filePath = file.path;
  const objectName = path.basename(file.originalname);
  
  try {
    // Read the file and prepare for upload
    const fileStream = fs.createReadStream(filePath);
    const uploadDetails = {
      namespaceName: namespaceName,
      bucketName: bucketName,
      objectName: objectName,
      putObjectBody: fileStream,
    };

    // Upload the file
    await client.putObject(uploadDetails);
    
    // Render the response
    res.render('upload', { objs: [], upload: 'File uploaded successfully' });
  } catch (error) {
    res.status(500).send('Error uploading file');
  } finally {
    // Delete the temporary file after upload
    fs.unlink(filePath, err => err && console.error('Error deleting temp file:', err));
  }
}

/**
 * Searches for documents in OpenSearch based on the input query and renders the results.
 * 
 * @param {Object} req - Express request object containing the search query in the body.
 * @param {Object} res - Express response object used to render the search results.
 */
async function fn_search(req, res) {
  let search = req.body.search || "";

  try {
    // Construct the OpenSearch query
    const query = {
      "query": {
        "query_string": {
          "query": "*"+ search +"*",
          "fields": ["obj_content"]
        }
      },
      "sort": [
        { "obj_name": { "order": "asc" }},
        { "obj_page": { "order": "asc" }}
      ]
    };
    
    // Send the query to OpenSearch and get the response
    const response = await axios.post(opensearch, query, { headers: { 'Content-Type': 'application/json' }, auth: { username, password } });

    // Extract the relevant documents from the response
    const objs = response.data.hits.hits.map(hit => hit._source);
    
    // Render the search results
    res.render('search', { objs, search });
  } catch (error) {
    res.status(500).send('Error retrieving search');
  }
}

/**
 * Retrieves documents from OpenSearch and renders the chat view with the documents and chat history.
 * 
 * @param {Object} req - Express request object.
 * @param {Object} res - Express response object.
 * @param {Array} jsonChat - Array containing chat history.
 * @param {String} [selectedDocument=null] - Optional selected document URL to be highlighted in the view.
 */
async function fn_files(req, res, jsonChat, selectedDocument = null) {
  let result;
  
  try {
    // Construct the OpenSearch query
    const query = {
      "_source": ["obj_name", "obj_url"],
      "query": {
        "bool": {
          "must": [
            { "match_all": {} },
            { "term": { "obj_page": 1 } }
          ]
        }
      }
    };
    
    // Send the query to OpenSearch and get the response
    const response = await axios.post(opensearch, query, { headers: { 'Content-Type': 'application/json' }, auth: { username, password } });
    
    // Extract the relevant documents from the response
    result = response.data.hits.hits.map(hit => hit._source);
  } catch (error) {
    res.status(500).send('Error retrieving files: ', error);
  } finally {
    // Render the chat view with the documents and chat history
    res.render('chat', { documents: result, chat: jsonChat, selectedDocument });
 }
}

/**
 * Processes a chat request by sending a question and document URL to a model endpoint, then updates and renders the chat view.
 * https://docs.public.oneportal.content.oci.oraclecloud.com/en-us/iaas/Content/API/Concepts/signingrequests.htm#seven__JavaScript
 * 
 * @param {Object} req - Express request object containing the question and document URL in the body.
 * @param {Object} res - Express response object used to render the updated chat view.
 */
async function fn_chat(req, res) {
  let result;
  const { document: url_document, question } = req.body;
  
  try {
    // Create the request body
    const data = {
      input: [
          question,
          url_document
      ]
    };
    
    // Convert the body to JSON
    const body = JSON.stringify(data);

    // Create HttpRequest to be signed
    const httpRequest = {
      uri: modelEndpoint,
      headers: new Headers({
        'Content-Type': 'application/json'
      }),
      method: "POST",
      body: body
    };
    
    // Sign the request
    await signer.signHttpRequest(httpRequest);

    // Make the call
    const response = await fetch(
      new Request(httpRequest.uri, {
        method: httpRequest.method,
        headers: httpRequest.headers,
        body: httpRequest.body
      })
    );

    // Get Model
    if (response.status === 404) {
      result = "<a class='w3-small color-r'>Modelo No disponible...</a>";
    } else if (response.ok) {
      result = (await response.json()).prediction;
    } else {
      result = `Error: <a class='w3-small color-r'>${response.statusText}</a>`;
    }    
 } catch (error) {
    console.error('Error:', error);
    result = error.message.toString();
 } finally {
    // Add the question and answer to the chat history
    jsonChat.push({
       question: req.body.question + "<br/><a class='w3-small color-r'>" + url_document.split('/').pop() + "</a>",
       answer: result
    });
    
    // Render the updated chat view with the new data
    fn_files(req, res, jsonChat, url_document);
 }
}

// Start the Server
app.listen(3000, ()=> { 
  console.log("server started on port 3000")
});