let dogs = [];

fetch("dogs.json")
.then(r => r.json())
.then(data => dogs = data);

const input = document.querySelector(".search-bar input");

input.addEventListener("input", () => {

  const val = input.value.toLowerCase();

  const results = dogs.filter(d =>
    d.name.toLowerCase().includes(val)
  );

  const container = document.getElementById("searchResults");
  container.innerHTML = "";

  results.forEach(d => {

    const el = document.createElement("div");
    el.className = "card";
    el.innerText = d.name + " (" + d.type + ")";

    el.onclick = () => {
      window.location.href = `${d.type}.html?id=${d.id}`;
    };

    container.appendChild(el);

  });

});
