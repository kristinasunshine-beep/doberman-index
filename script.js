fetch('data/dogs.json')
  .then(res => res.json())
  .then(data => {
    const container = document.getElementById('dogsContainer');

    data.forEach(dog => {
      const card = document.createElement('div');
      card.className = 'card';

      card.innerHTML = `
        <img src="${dog.image}">
        <h3>${dog.name}</h3>
        <p>${dog.pedigree}</p>
        <p>${dog.price}</p>
        <a href="${dog.contact}" target="_blank">Contact</a>
      `;

      container.appendChild(card);
    });
  });

/* cursor */
const cursor = document.querySelector('.cursor');

document.addEventListener('mousemove', e => {
  cursor.style.top = e.clientY + 'px';
  cursor.style.left = e.clientX + 'px';
});
