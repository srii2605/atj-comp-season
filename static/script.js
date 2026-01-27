document.addEventListener("DOMContentLoaded", function () {
    fetch("/data")
        .then(response => response.json())
        .then(data => {
            const tableBody = document.querySelector("#data-table tbody");
            tableBody.innerHTML = "";

            data.forEach(row => {
                let tr = document.createElement("tr");

                tr.innerHTML = `
                    <td>${row.name}</td>
                    <td>${row.date}</td>
                    <td>${row.time}</td>
                    <td><img src="${row.costume}" alt="Costume" width="100"></td>
                `;

                tableBody.appendChild(tr);
            });
        })
        .catch(error => console.error("Error fetching data:", error));
});
Sc