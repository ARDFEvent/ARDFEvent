async function get(url) {
    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`Response status: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error(error.message);
    }
}

async function setup() {
    const announcement = await get("/api/announcement");
    document.querySelector("#name").innerText = announcement["name"];
    document.querySelector("#date").innerText = announcement["date_tzero"];

    if (announcement["ann"]) {
        document.querySelector("#alert").style.display = "block";
        document.querySelector("#alert-text").innerText = announcement["ann"];
    } else {
        document.querySelector("#alert").style.display = "none";
    }

    document.querySelector("#categories").innerHTML = "";
    const cats = await get("/api/categories")
    for (const cat of Object.keys(cats)) {
        document.querySelector("#categories").innerHTML += `<a class="${cat.startsWith("M") ? "men" : cat.startsWith("D") ? "women" : "other"}" href="vysledky.html?cat=${cat}">${cat}</a>`;
    }
}

setup();