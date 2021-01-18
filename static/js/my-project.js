const fileLabel = document.querySelector('.custom-file-label');
const reducedText = `${fileLabel.textContent.substr(0, 30)}...`;
fileLabel.innerHTML = reducedText;