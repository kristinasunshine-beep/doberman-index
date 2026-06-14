const input = document.getElementById("search");

const data = [
  "Dion Dante (Stud)",
  "Athena Black Line (Female)",
  "Lionsign Kennel",
  "AI Pedigree Report",
  "Stud Promotion Kit"
];

input.addEventListener("input", () => {

  const val = input.value.toLowerCase();

  const results = data.filter(d =>
    d.toLowerCase().includes(val)
  );

  const container = document.getElementById("searchResults");
  container.innerHTML = "";

  results.forEach(r => {
    const div = document.createElement("div");
    div.className = "card";
    div.innerText = r;
    container.appendChild(div);
  });

});
