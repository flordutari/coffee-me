const cardProjectDescription = document.querySelectorAll('.COF-card-project-description');

[...cardProjectDescription].forEach(card => {
    const reducedText = card && `${card.textContent.substr(0, 120)}...`;
    if (card) card.innerHTML = reducedText;
});
