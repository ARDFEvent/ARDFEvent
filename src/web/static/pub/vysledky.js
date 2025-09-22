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

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

async function mainProc() {
    const cat = new URLSearchParams(new URL(window.location).search).get("cat");

    const results_elem = document.querySelector("#results");

    while (true) {
        const announcement = await get("/api/announcement");
        document.querySelector("#name").innerText = `${announcement["name"]} - ${cat}`;
        if (announcement["ann"]) {
            document.querySelector("#alert").style.display = "block";
            document.querySelector("#alert-text").innerText = announcement["ann"];
        } else {
            document.querySelector("#alert").style.display = "none";
        }

        let results = await get(`/api/results?category=${cat}`);
        results_elem.innerHTML = "";

        if (results.length === 0) {
            results_elem.innerHTML = `<tr><td class="place"><b>🛌🏿</b></td><td><b>Žádní závodníci</b></tr>`;
            document.querySelector("#last_update").innerHTML = "-";
            return;
        }

        for (const result of results) {
            let place = result.place > 0 ? result.place > 4 ? `${result.place}.` : ["🥇", "🥈", "🥉", "🥔"][result.place - 1] : result.time === "UNS" ? "🛌🏿" : result.status === "?" ? "🏃🏾‍➡️" : result.status;
            const in_forest = result.status === "?";
            const show_info = ["OK", "OVT", "MP"].includes(result.status);
            const ok = result.status === "OK";
            const order = result.order.map((x) => `<b>${x[0]}</b>`).join(", ");
            results_elem.innerHTML += `<tr><td class="place"><b>${place}</b></td><td><b>${result.name}${result.index === "ELB0904" ? " 👨🏿‍💻" : result.index === "AFK1003" ? " 🎨" : ""}</b></td><td class="time"><b>${!ok && show_info ? `<span class="invalid">` : ""}${in_forest ? `<span class="temp_res">` : ""}${!(show_info || in_forest) ? "" : result.time === "UNS" ? `S: ${result.start}` : result.time}${in_forest ? "</span>" : ""}${!ok && show_info ? `</span>` : ""}</b></td></tr><tr class="secondline"><td></td><td>${!ok && show_info ? `<span class="invalid">` : ""}${show_info ? order : ""}${!ok && show_info ? `</span>` : ""}</td><td class="tx"><b>${!ok && show_info ? `<span class="invalid">` : ""}${show_info ? `${result.tx} TX` : "-"}${!ok && show_info ? `</span>` : ""}</b></td></tr>`
        }

        document.querySelector("#last_update").innerHTML = new Date(Date.now()).toLocaleTimeString("cs-CZ");
        await sleep(15000);
    }
}

mainProc();