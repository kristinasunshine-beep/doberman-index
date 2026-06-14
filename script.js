const input = document.getElementById("search");

const data = [
  { name: "Dion Dante", target: "#stud" },
  { name: "Athena Black Line", target: "#female" },
  { name: "Lionsign Kennel", target: "#kennel" },
  { name: "AI Pedigree Report", target: "#services" }
];

input.addEventListener("input", () => {

  const val = input.value.toLowerCase();

  const results = data.filter(d =>
    d.name.toLowerCase().includes(val)
  );

  const container = document.getElementById("searchResults");
  container.innerHTML = "";

  results.forEach(r => {

    const div = document.createElement("div");
    div.className = "card";
    div.innerText = r.name;

    div.onclick = () => {
      document.querySelector(r.target).scrollIntoView({
        behavior: "smooth"
      });
    };

    container.appendChild(div);

  });

});
