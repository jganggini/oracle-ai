const express = require("express");
const oracledb = require("oracledb");
const http = require("http");
const path = require("path");
const dotenv = require("dotenv");
const bodyParser = require("body-parser");
const helmet = require("helmet");
const rateLimit = require("express-rate-limit");
const puppeteer = require('puppeteer');

const app = express();

dotenv.config({ path: "./.env"});

const limiter = rateLimit({
   windowMs: 15 * 60 * 1000, // 15 minutes
   max: 100 // limit each IP to 100 requests per windowMs
});

const dir = path.join(__dirname, "./public")

app.use(bodyParser.json());
app.use(express.static(dir))
app.use(express.urlencoded({extended: false}))
app.use(express.json())
app.use(helmet({
      contentSecurityPolicy: false,
}))
app.use(limiter);

app.set("view engine", "hbs")

//get
app.get("/", (req, res) => { res.render("index") })
app.get("/adai", (req, res) => { res.render("adai") })
app.get("/adaiava", (req, res) => { res.render("adaiava") })
app.get("/acaiava", (req, res) => { res.render("acaiava") })


//adai
jsonData = [];
class_css = "";

app.post("/adai", (req, res) => {
   fn_adai(req, res)
})

async function fn_adai(req, res)
{
   try {
      // Use the connection string copied from the cloud console
      // and stored in connstring.txt file from Step 2 of this tutorial
      connection = await oracledb.getConnection({connectionString: process.env.DATABASE_CONNECTIONSTRING,
                                                 user: process.env.DATABASE_USER,
                                                 password: process.env.DATABASE_PASSWORD
                                                });
      
      //Type
      sql = "SELECT AI " + req.body.parameter + " " + req.body.question;
      class_css = (req.body.parameter == "SHOWSQL" ? "w3-code" : "");
      //Autonomous
      result = await connection.execute(sql);
      result = result.rows.toString();

   } catch (err) {
      result = err.message.toString();
       console.error(err);
   } finally {
      if (connection) {
         try {
               await connection.close();
             } catch (err) {
               result = err.message.toString();
               console.error(err.message);
         }
      }

      //Add data to list
      jsonData.push({
         question: req.body.question,
         result: result,
         w3_code: class_css
      });
      return res.render("adai", {
         chat: jsonData
      })
   }
}

//acaiva
app.get('/adaiava.send', (req, res) => {
   var display;

   if (req.query.question !== "") {
      display = "none";
      fn_adaiava(req, res);
   } else {
      res.json({ display: "block", message: "Enter your question..." });
   }
})

async function fn_adaiava(req, res)
{
   try {
      // Use the connection string copied from the cloud console
      // and stored in connstring.txt file from Step 2 of this tutorial
      connection = await oracledb.getConnection({connectionString: process.env.DATABASE_CONNECTIONSTRING,
                                                 user: process.env.DATABASE_USER,
                                                 password: process.env.DATABASE_PASSWORD
                                                });
      
      //Type
      sql = "SELECT AI NARRATE " + req.query.question;
      //Autonomous
      result = await connection.execute(sql);
      result = result.rows.toString();
   } catch (err) {
      res.json({ display:"block", message: err.message.toString() });
   } finally {
      if (connection) {
         try {
               await connection.close();
             } catch (err) {
               res.json({ display:"block", message: err.message.toString() });
         }
      }
      res.json({ display: "none", message: "", result: result });      
   }
}













app.listen(3000, ()=> {
    console.log("server started on port 3000")
});