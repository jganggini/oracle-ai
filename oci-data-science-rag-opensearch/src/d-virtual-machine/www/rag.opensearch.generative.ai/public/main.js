// Function that displays a loading screen
function showLoading() {
    document.getElementById("loadingScreen").style.display = "block";
}

// Function to set the active link based on the current URL path
function setActiveLink() {
    const path = window.location.pathname;
    const links = {
        '/': document.getElementById('home-link'),
        '/upload': document.getElementById('upload-link'),
        '/search': document.getElementById('search-link'),
        '/chat': document.getElementById('chat-link'),
    };
    
    if (links[path]) {
        links[path].classList.add('active');
    }
}
window.onload = setActiveLink;