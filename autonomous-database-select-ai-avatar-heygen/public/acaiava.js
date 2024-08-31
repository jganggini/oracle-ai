"use strict";

const pathname = window.location.pathname;

document
   .querySelector("#start")
   .addEventListener("click", startHandler);

switch (pathname) {
  case '/acaiava':
    document
   .querySelector("#talk")
   .addEventListener("click", talkHandler);
  case '/adaiava':
   
}



document
   .querySelector("#repeat")
   .addEventListener("click", repeatHandler);

document
   .querySelector("#close")
   .addEventListener("click", closeConnectionHandler);

async function startHandler() {
  try {
    //Analytics Cloud: Natural Language Generation (NLG)
    // Selecciona el contenido del div
    const pathname = window.location.pathname;    
    const taskInput = document.getElementById('taskInput');

    switch (pathname) {
      case '/acaiava':
        const contentDiv = document.getElementById('view!3pane-contentpane_11-vizCont');
        const content = (contentDiv.textContent || contentDiv.innerText).replace(/(\r\n|\n|\r)/gm, "");
        taskInput.value = content.replace(/\s+/g, ' ').trim();
        document.getElementById('translateTo').disabled = true;
        document.getElementById('talk').disabled = false;
      case '/adaiava':
        
    }        

    //HeyGen
    await createNewSession();
    await startAndDisplaySession();

    document.getElementById('start').disabled = true;
    document.getElementById('repeat').disabled = false;
    document.getElementById('close').disabled = false;
  } catch (error) {
    console.log('Error:', error.message);
    updateStatus(statusElement, error.message)
  }
}
// new session
async function traslatorHandler(text) {
  const translateFrom = "en";
  const translateTo = document.getElementById('translateTo').value;

  updateStatus(statusElement, "Translating dialog... please wait");

  if (translateFrom !== translateTo) {
    const response = await fetch(`https://translated-mymemory---translation-memory.p.rapidapi.com/get?langpair=${translateFrom}|${translateTo}&q=${text}&mt=1&onlyprivate=0&de=a%40b.c`, {
      method: "GET",
      headers: {
        'X-RapidAPI-Key': '********',
        'X-RapidAPI-Host': 'translated-mymemory---translation-memory.p.rapidapi.com'
      }
    });
    if (response.status !== 200) {
      console.error("Server error");
      updateStatus(statusElement, "Server Error. Please ask the staff if the service has been turned on");
      throw new Error("Server error");
    } else {
      const data = await response.json();
      return data.responseData.translatedText;
    }
  } else {
    updateStatus(statusElement, "Translated dialogue successfully");
    return text;
  }
}

//HeyGen

import heygen_API from "./api.json" assert { type: "json" };

const statusElement = document.querySelector("#status");
const apiKey = heygen_API.apiKey;
const SERVER_URL = heygen_API.serverUrl;
const avatarName = "";
const voiceName = "";

if (apiKey === "YourApiKey" || SERVER_URL === "") {
  alert("Please enter your API key and server URL in the api.json file");
}

let sessionInfo = null;
let peerConnection = null;

function updateStatus(statusElement, message) {
  statusElement.innerHTML += message + "<br>";
  statusElement.scrollTop = statusElement.scrollHeight;
}

updateStatus(
  statusElement,
  "Please click the Start button to create the stream first."
);

// Create a new WebRTC session when clicking the "New" button
async function createNewSession() {
  updateStatus(statusElement, "Creating new session... please wait");

  // call the new interface to get the server's offer SDP and ICE server to create a new RTCPeerConnection
  sessionInfo = await newSession("high", avatarName, voiceName);
  const { sdp: serverSdp, ice_servers: iceServers } = sessionInfo;

  // Create a new RTCPeerConnection
  peerConnection = new RTCPeerConnection({ iceServers: [] });
  let formattedIceServers = iceServers.map((server) => ({ urls: server }));
  peerConnection.setConfiguration({ iceServers: formattedIceServers });

  // When ICE candidate is available, send to the server
  peerConnection.onicecandidate = ({ candidate }) => {
    console.log("Received ICE candidate:", candidate);
    if (candidate) {
      handleICE(sessionInfo.session_id, candidate.toJSON());
    }
  };

  // When ICE connection state changes, display the new state
  peerConnection.oniceconnectionstatechange = (event) => {
    updateStatus(statusElement, `ICE connection state changed to: ${peerConnection.iceConnectionState}`);
  };

  // When audio and video streams are received, display them in the video element
  const mediaElement = document.querySelector("#mediaElement");
  peerConnection.ontrack = (event) => {
    console.log("Received the track");
    if (event.track.kind === "audio" || event.track.kind === "video") {
      mediaElement.srcObject = event.streams[0];
    }
  };

  // Set server's SDP as remote description
  const remoteDescription = new RTCSessionDescription(serverSdp);
  await peerConnection.setRemoteDescription(remoteDescription);

  updateStatus(statusElement, "Session creation completed");
}

// Start session and display audio and video when clicking the "Start" button
async function startAndDisplaySession() {
  if (!sessionInfo) {
    updateStatus(statusElement, "Please create a connection first");
    return;
  }

  updateStatus(statusElement, "Starting session... please wait");

  // Create and set local SDP description
  const localDescription = await peerConnection.createAnswer();
  await peerConnection.setLocalDescription(localDescription);

  // Start session
  await startSession(sessionInfo.session_id, localDescription);
  updateStatus(statusElement, "Session started successfully");
}

// When clicking the "Send Task" button, get the content from the input field, then send the tas
async function talkHandler() {
  const taskInput = document.getElementById('taskInput');
  
  if (!sessionInfo) {
    updateStatus(statusElement, "Please create a connection first");
    return;
  }
  updateStatus(statusElement, "Sending task... please wait");
  const text = taskInput.value;
  if (text.trim() === "") {
    alert("Please enter a task");
    return;
  }

  //Traslator
  const traslator = await traslatorHandler(text);

  console.log(traslator);

  const resp = await talk(sessionInfo.session_id, traslator);

  updateStatus(statusElement, "Task sent successfully");
}

// When clicking the "Send Task" button, get the content from the input field, then send the tas
async function repeatHandler() {
  if (!sessionInfo) {
    updateStatus(statusElement, "Please create a connection first");
    return;
  }
  updateStatus(statusElement, "Sending task... please wait");
  
  console.log("--taskInput--");
  console.log(taskInput.value);

  const text = taskInput.value;
  if (text.trim() === "") {
    alert("Please enter a task");
    return;
  }

  const resp = await repeat(sessionInfo.session_id, text);

  updateStatus(statusElement, "Task sent successfully");
}

// when clicking the "Close" button, close the connection
async function closeConnectionHandler() {
  if (!sessionInfo) {
    updateStatus(statusElement, "Please create a connection first");
    return;
  }
  updateStatus(statusElement, "Closing connection... please wait");
  try {
    // Close local connection
    peerConnection.close();
    // Call the close interface
    const resp = await stopSession(sessionInfo.session_id);

    console.log(resp);
  } catch (err) {
    console.error("Failed to close the connection:", err);
  }
  updateStatus(statusElement, "Connection closed successfully");

  switch (pathname) {
    case '/acaiava':
      document.getElementById('translateTo').disabled = false;
      document.getElementById('talk').disabled = true;
    case '/adaiava':
      
  }   

  document.getElementById('start').disabled = false;  
  document.getElementById('repeat').disabled = true;
  document.getElementById('close').disabled = true;
}

// new session
async function newSession(quality, avatar_name, voice_name) {
  const response = await fetch(`${SERVER_URL}/v1/realtime.new`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Api-Key": apiKey,
    },
    body: JSON.stringify({ quality }), // joel.ganggini [demo]
  });
  if (response.status !== 200) {
    console.error("Server error");
    updateStatus(
      statusElement,
      "Server Error. Please ask the staff if the service has been turned on"
    );

    throw new Error("Server error");
  } else {
    const data = await response.json();
    console.log(data.data);
    return data.data;
  }
}

// start the session
async function startSession(session_id, sdp) {
  const response = await fetch(`${SERVER_URL}/v1/realtime.start`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Api-Key": apiKey,
    },
    body: JSON.stringify({ session_id, sdp }),
  });
  if (response.status === 500) {
    console.error("Server error");
    updateStatus(
      statusElement,
      "Server Error. Please ask the staff if the service has been turned on"
    );
    throw new Error("Server error");
  } else {
    const data = await response.json();
    return data.data;
  }
}

// submit the ICE candidate
async function handleICE(session_id, candidate) {
  const response = await fetch(`${SERVER_URL}/v1/realtime.ice`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Api-Key": apiKey,
    },
    body: JSON.stringify({ session_id, candidate }),
  });
  if (response.status === 500) {
    console.error("Server error");
    updateStatus(
      statusElement,
      "Server Error. Please ask the staff if the service has been turned on"
    );
    throw new Error("Server error");
  } else {
    const data = await response.json();
    return data;
  }
}

async function talk(session_id, text) {
  const task_type = "talk";

  const response = await fetch(`${SERVER_URL}/v1/realtime.task`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Api-Key": apiKey,
    },
    body: JSON.stringify({ session_id, text, task_type }),
  });
  if (response.status === 500) {
    console.error("Server error");
    updateStatus(statusElement, "Server Error. Please ask the staff if the service has been turned on");
    throw new Error("Server error");
  } else {
    const data = await response.json();
    return data.data;
  }
}

// repeat the text
async function repeat(session_id, text) {
  const task_type = "repeat";
  const response = await fetch(`${SERVER_URL}/v1/realtime.task`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Api-Key": apiKey,
    },
    body: JSON.stringify({ session_id, text, task_type }),
  });
  if (response.status === 500) {
    console.error("Server error");
    updateStatus(
      statusElement,
      "Server Error. Please ask the staff if the service has been turned on"
    );
    throw new Error("Server error");
  } else {
    const data = await response.json();
    return data.data;
  }
}

// stop session
async function stopSession(session_id) {
  const response = await fetch(`${SERVER_URL}/v1/realtime.stop`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Api-Key": apiKey,
    },
    body: JSON.stringify({ session_id }),
  });
  if (response.status === 500) {
    console.error("Server error");
    updateStatus(statusElement, "Server Error. Please ask the staff for help");
    throw new Error("Server error");
  } else {
    const data = await response.json();
    return data.data;
  }
}