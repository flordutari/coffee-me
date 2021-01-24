const cardProjectDescription = document.querySelectorAll('.COF-card-project-description');
const coffeeValueButtons = document.querySelectorAll('.COF-primary-box');
const coffeesQuantityInput = document.querySelector('#coffeesQuantity');

[...cardProjectDescription].forEach(card => {
    const reducedText = card && `${card.textContent.substr(0, 120)}...`;
    if (card) card.innerHTML = reducedText;
});

coffeeValueButtons.forEach(button => {
    button.addEventListener('click', e => {
        e.preventDefault();
        coffeesQuantityInput.value = e.target.textContent;
    });
});