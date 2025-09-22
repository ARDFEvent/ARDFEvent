getData();

async function getData() {
    const url = "/api/categories";
    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`Response status: ${response.status}`);
        }

        const result = await response.json();
        const cats = document.querySelector("#categories");
        cats.setAttribute("size", Object.keys(result).length.toString());
        for (const key of Object.keys(result)) {
            cats.innerHTML += `<option value="${key}">${key}</option>`
        }
    } catch (error) {
        console.error(error.message);
    }
}
