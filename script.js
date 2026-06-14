let dogs = [];

fetch("dogs.json")
.then(r => r.json())
.then(data => dogs = data);

const input = document.querySelector(".search-wrap input");

input.addEventListener("input", () => {

  const val = input.value.toLowerCase();

  const results = dogs.filter(d =>
    d.name.toLowerCase().includes(val) ||
    d.type.toLowerCase().includes(val)
  );

  const container = document.getElementById("searchResults");
  container.innerHTML = "";

  results.forEach(d => {

    const el = document.createElement("div");
    el.className = "card";
    el.innerText = d.name + " (" + d.type + ")";

    el.addEventListener("mouseenter", () => {
      renderPreview(d);
    });

    el.onclick = () => {
      window.location.href = `${d.type}.html?id=${d.id}`;
    };

    container.appendChild(el);

  });

});

function renderPreview(d){

  const preview = document.getElementById("preview");
  preview.innerHTML = "";

  const img = document.createElement("div");
  img.className = "preview-img";
  img.style.backgroundImage = `url(${d.image})`;

  const title = document.createElement("div");
  title.className = "preview-title";
  title.innerText = d.name;

  const type = document.createElement("div");
  type.className = "preview-type";
  type.innerText = d.type.toUpperCase();

  const chips = document.createElement("div");
  chips.className = "chips";

  (d.genetics || []).forEach(g => {
    const s = document.createElement("span");
    s.innerText = g;
    chips.appendChild(s);
  });

  const info = document.createElement("div");
  info.style.marginTop = "10px";
  info.innerText =
    "Litters: " + (d.litters || "—");

  preview.appendChild(img);
  preview.appendChild(title);
  preview.appendChild(type);
  preview.appendChild(chips);
  preview.appendChild(info);
}
