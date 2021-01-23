const fileLabel = document.querySelector('.custom-file-label');
const reducedText = fileLabel && `${fileLabel.textContent.substr(0, 30)}...`;
if (fileLabel) fileLabel.innerHTML = reducedText;