async function postData(url) {
    try {
        const response = await fetch(url, { method: "POST" });
        const data = await response.json();
        document.getElementById("status").innerText = data.status;
        document.getElementById("status").style.display = 'block';
        document.getElementById("status").style.top = '20px'; 

        setTimeout(() => {
            document.getElementById("status").style.top = '-20px'; 
            document.getElementById("status").style.display = 'none'; 
        }, 2000);

    } catch (error) {
        document.getElementById("status").innerText = "Error communicating with backend.";
        console.error(error);
    }
}

document.getElementById("home-link").addEventListener("click", function (e) {
    e.preventDefault();
    window.location.href = "/";
});

document.getElementById("year").textContent = new Date().getFullYear();
document.getElementById("trigger-alert").addEventListener("click", () => postData("/trigger"));
document.getElementById("stop-alert").addEventListener("click", () => postData("/stop"));
document.getElementById("start-backend").addEventListener("click", () => postData("/start_backend"));
document.getElementById("stop-backend").addEventListener("click", () => postData("/stop_backend"));

// char moving effect
const line1 = document.getElementById('line1');
const line2 = document.getElementById('line2');
const usernameContainer = document.getElementById('username-container');
const username = usernameContainer.dataset.username;
// console.log(`Username: ${username}`);


const texts = [
    `Welcome to Email Bot ${username}`,   
    "You Can Sleep Peacefully While I am Awake for you."  
];

let charIndex = [0, 0]; 
let lineIndex = 0;  
let typing = true;  

function addChar() {
    if (!typing) return;  

    line1.textContent = texts[0].slice(0, charIndex[0] + 1);  
    line2.textContent = texts[1].slice(0, charIndex[1] + 1);  

    if (charIndex[lineIndex] < texts[lineIndex].length - 1) {
        charIndex[lineIndex]++;
        setTimeout(addChar, 50);  
    } else {
        if (lineIndex === 0) {
            line2.style.visibility = 'visible';
            lineIndex = 1;  
            charIndex[1] = 0;  
            setTimeout(addChar, 50);  
        } else {
            setTimeout(() => {
                charIndex = [0, 0];  
                lineIndex = 0;  
                line1.style.visibility = 'visible';  
                line2.style.visibility = 'hidden';  
                addChar();  
            }, 500);  
        }
    }
}

// Start the typing effect
line1.style.visibility = 'visible';  
addChar();

// sidebar logic - SHOW
document.getElementById("SidebarVisible").onclick = function () {
    document.getElementById("ReportSidebarWrap").classList.add("visibilityWrap");
    document.getElementById("ReportSidebar").classList.add("newsfeedtop");
    document.getElementById("ConfigDialogue").style.display = 'none';
    document.getElementById("form-container").style.display = 'none';
    typing = false;
    line1.textContent = '';  
    line2.textContent = '';  
};
// sidebar logic - HIDE
document.getElementById("cartClose").onclick = function () {
    document.getElementById("ReportSidebarWrap").classList.remove("visibilityWrap");
    document.getElementById("ReportSidebar").classList.remove("newsfeedtop");
    document.getElementById("ConfigDialogue").style.display = 'block';
    typing = true;  
    addChar();  
};

// form visibility
document.getElementById("formClose").onclick = function () {
    document.getElementById("form-container").style.display = 'none';
    document.getElementById("typing-effect").style.display = 'block';
};

document.getElementById("formOpen").onclick = function () {
    document.getElementById("form-container").style.display = 'block';
    // document.getElementsByClassName("dialog-boxNew").style.display = 'none';
    document.getElementById("typing-effect").style.display = 'none';
    document.getElementById("ConfigDialogue").style.display = 'none';
}

//  polling error dialogue box////////////////////////////////

// Function to fetch errors from the backend every 10 seconds
async function pollForErrors() {
    console.log("Polling for errors..."); 
    try {
      const response = await fetch("/error", {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
      });
  
      if (!response.ok) {
        console.error(`Error: Received HTTP ${response.status} from the server.`);
        return;
      }
  
      const data = await response.json();
      console.log("Received response:", data); 
  
      if (data.status === "Error available" && data.message) {
        console.log("Error found, showing dialog."); 
        const dialog = document.getElementById("error-dialog");
        const messageElement = document.getElementById("error-message");
  
        if (!dialog || !messageElement) {
          console.error("Dialog or message element not found in the DOM.");
          return;
        }
  
        messageElement.textContent = data.message;
        dialog.style.display="block";
      } else {
        console.log("No error available."); 
      }
    } catch (error) {
      console.error("Error while polling for errors:", error); 
    }
  }
  
  // Function to dismiss the error dialog
  function dismissDialog() {
    console.log("Dismissing dialog box..."); 
    const dialog = document.getElementById("error-dialog");
    if (!dialog) {
      console.error("Dialog element not found in the DOM.");
      return;
    }
    dialog.style.display="none";
  }
  
  setInterval(async () => {
    console.log("Running scheduled poll..."); 
    const dialog = document.getElementById("error-dialog");
  
    if (!dialog) {
      console.error("Dialog element not found in the DOM.");
      return;
    }
  
    if (!dialog.classList.contains("show")) {
      await pollForErrors();
    } else {
      console.log("Dialog is already shown, skipping poll.");
    }
  }, 10000);
  
  // Initial poll
  pollForErrors();


// pull-config in form
const toggleConfig = document.getElementById('toggleConfig');
const emailInput = document.getElementById('email');
const appPasswordInput = document.getElementById('app-password');
const manualEntryInput = document.getElementById('manual-entry');

toggleConfig.addEventListener('change', async function () {
    try {
        const isChecked = this.checked;
        
        if (isChecked) {
            const response = await fetch("/get_latest_config", {
                method: "GET",
                headers: {
                    "Content-Type": "application/json"
                },
            });

            if (response.ok) {
                const data = await response.json();
                console.log("Response Data:", data);

                emailInput.value = data.email_id || "";
                appPasswordInput.value = data.app_password || "";
                
                if (Array.isArray(data.mail_to_check)) {
                    manualEntryInput.value = data.mail_to_check.join(", ");
                } else {
                    manualEntryInput.value = "";
                }
            } else {
                alert("configuration not present inside DB, Please add First!");
            }
        } else {
            emailInput.value = "";
            appPasswordInput.value = "";
            manualEntryInput.value = "";
        }
    } catch (error) {
        console.error("Error Fetching Config:", error);
        alert("Error fetching configuration.");
    }
});

// password visibility
function togglePasswordVisibility() {
    const passwordInput = document.getElementById('app-password');
    // const eyeIcon = document.getElementById('eyeIcon');
    const eyeImg = document.getElementById('eyeImg');
    
    if (passwordInput.type === 'password') {
      passwordInput.type = 'text';
      eyeImg.src = '/static/output-onlinegiftools.gif';
    } else {
      passwordInput.type = 'password';
      eyeImg.src = '/static/output-onlinegiftools.gif';
    }
  }

/////////////////////////////// filtering of the reports ///////////////////////////

const reportContainer = document.getElementById("report-container");
const filterReportRadios = document.querySelectorAll("input[name='filter']");
const sidebarUl = document.querySelector(".sidebar ul");

function updateReports(data) {
    sidebarUl.innerHTML = "";
    reportContainer.innerHTML = "";

    const sortedDates = Object.keys(data).sort((a, b) => {
        const dateA = parseDate(a);
        const dateB = parseDate(b);
        return dateA - dateB;
    });

    sortedDates.forEach(date => {
        const entries = data[date];

        const dateLink = document.createElement("li");
        dateLink.innerHTML = `<a href="#" class="date-link" data-date="${date.replace(/[\s:,+-]/g, '')}">${date}</a>`;
        sidebarUl.appendChild(dateLink);

        const reportSection = document.createElement("div");
        reportSection.id = `report-${date.replace(/[\s:,+-]/g, '')}`;
        reportSection.classList.add("report-section");
        reportSection.style.display = "none";

        reportSection.innerHTML = `
            <h2>${date}</h2>
            <table>
                <thead>
                    <tr>
                        <th>From</th>
                        <th>Subject</th>
                        <th>Date & Time</th>
                    </tr>
                </thead>
                <tbody>
                    ${entries
                        .map(
                            entry =>
                                `<tr>
                                    <td>${entry.from_email}</td>
                                    <td>${entry.subject}</td>
                                    <td>${entry.mail_datetime}</td>
                                </tr>`
                        )
                        .join("")}
                </tbody>
            </table>
        `;

        document.getElementById("hiddenul").appendChild(reportSection); 
    });

    initDateLinkEvents();
}

function parseDate(dateStr) {
    const dailyFormat = /^\d{2} [A-Za-z]{3} \d{4}$/; // Example: "01 Aug 2024"
    const monthlyFormat = /^[A-Za-z]+ \d{4}$/; // Example: "August 2024"
    const yearlyFormat = /^\d{4}$/; // Example: "2024"

    if (dailyFormat.test(dateStr)) {
        return new Date(dateStr); 
    } else if (monthlyFormat.test(dateStr)) {
        return new Date(`01 ${dateStr}`); 
    } else if (yearlyFormat.test(dateStr)) {
        return new Date(`01 Jan ${dateStr}`); 
    } else {
        return new Date(); 
    }
}

async function fetchFilteredReports(filter) {
    try {
        const response = await fetch("/filter_reports", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ filter })
        });

        const data = await response.json();

        if (data.status === "success") {
            updateReports(data.reports); 
        } else {
            reportContainer.innerHTML = `<p>${data.message}</p>`;
        }
    } catch (error) {
        console.error("Error fetching filtered reports:", error);
        reportContainer.innerHTML = `<p>Error fetching reports.</p>`;
    }
}

function initDateLinkEvents() {
    const dateLinks = document.querySelectorAll(".date-link");

    dateLinks.forEach(link => {
        link.addEventListener("click", (e) => {
            e.preventDefault();
            const date = link.getAttribute("data-date");
            const reportSection = document.querySelector(`#report-${date}`);

            reportContainer.innerHTML = "";

            const allReportSections = document.querySelectorAll(".report-section");
            allReportSections.forEach(section => {
                section.style.display = "none";
            });

            if (reportSection) {
                reportContainer.appendChild(reportSection.cloneNode(true));
                reportContainer.style.display = "block";
                reportSection.style.display = "block";
            } else {
                reportContainer.innerHTML = `<p>No reports available for ${date}.</p>`;
            }
        });
    });
}

filterReportRadios.forEach(radio => {
    radio.addEventListener("change", (e) => {
        const filter = e.target.value; 
        fetchFilteredReports(filter);
    });
});

initDateLinkEvents();


