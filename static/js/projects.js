const cardProjectDescription = document.querySelectorAll('.COF-card-project-description');
const coffeeValueButtons = document.querySelectorAll('.COF-primary-box');
const coffeesQuantityInput = document.querySelector('#coffeesQuantity');
const buttonBuyCoffee = document.querySelector('#buyCoffee');
const inputCoffeesQuantity = document.querySelector('#coffeesQuantity');

[...cardProjectDescription].forEach(card => {
    const reducedText = card && `${card.textContent.substr(0, 120)}...`;
    if (card) card.innerHTML = reducedText;
});

coffeeValueButtons.forEach(button => {
    button.addEventListener('click', e => {
        e.preventDefault();
        const quantity = e.target.textContent;
        coffeesQuantityInput.value = quantity;
        if (e.target.textContent > 1) {
            buttonBuyCoffee.innerHTML = `Buy ${quantity} coffees (USD $${quantity * 3})`;
        } else {
            buttonBuyCoffee.innerHTML = 'Buy a coffee (USD $3)';
        }
    });
});

if (inputCoffeesQuantity) {
    inputCoffeesQuantity.addEventListener('keyup', e => {
        const quantity = e.target.value;
        if (quantity > 1) {
            buttonBuyCoffee.innerHTML = `Buy ${quantity} coffees (USD $${quantity * 3})`;
        } else {
            buttonBuyCoffee.innerHTML = 'Buy a coffee (USD $3)';
        }
    })
}