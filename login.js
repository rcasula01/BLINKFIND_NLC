// login.js
const API_BASE = window.API_BASE || (location.protocol + '//' + location.hostname + ':4000');

let loginAttempts = 0;


//grabs elements from the html file
const form = document.getElementById("loginForm");
const errorBox = document.getElementById("loginError");
const emailInput = document.getElementById("email");
const password = document.getElementById("password");
const rememberMe = document.getElementById("rememberMe");


// runs when the login form is submitted
form.addEventListener("submit", async e => {
  e.preventDefault();
  const email = emailInput.value.trim();
  const pass = password.value;
  const remember = rememberMe.checked;

  // Clear previous error
  errorBox.classList.remove("show");
  errorBox.textContent = "";

  try {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ email, password: pass })
    });

    const data = await res.json();

    if (res.ok && data.success) {
      // Persist remembered email (no passwords or tokens in localStorage)
      if (remember) {
        localStorage.setItem("rememberedEmail", email);
      } else {
        localStorage.removeItem("rememberedEmail");
      }
      console.log("Login successful");
      window.location.href = "./home.html";
    } else {
      loginAttempts++;
      errorBox.textContent = data.error || "Invalid email or password.";
      errorBox.classList.add("show");
      if (loginAttempts >= 3) {
        alert("Too many failed attempts. Please try again later.");
        loginAttempts = 0;
      }
    }
  } catch (err) {
    loginAttempts++;
    errorBox.textContent = "Unable to reach the server. Please try again.";
    errorBox.classList.add("show");
    console.error("Login error:", err);
  }
});


document.getElementById("forgotPassword").onclick = e => { e.preventDefault(); alert("Contact system administrator."); };

//when the page loads check if email is saved
window.onload = () => {
  const saved = localStorage.getItem("rememberedEmail");
  if (saved) { emailInput.value = saved; rememberMe.checked = true; }
};