document.addEventListener("DOMContentLoaded", function () {

  const wordBank = ["DEBUG", "INPUT", "LOGIC", "ARRAY", "EMAIL", "CACHE"];

  const gridCells = document.querySelectorAll(".container div");
  const ROW_LENGTH = 5;
  const MISSING_COUNT = 2;

  let allExpectedLetters = [];

  // how many rows your grid has
  const rows = Math.ceil(gridCells.length / ROW_LENGTH);

  // Shuffle a copy of the word bank so we get DIFFERENT words per row
  const shuffled = [...wordBank].sort(() => Math.random() - 0.5);

  // If you have more rows than words, this repeats only after exhausting all words
  const wordsForRows = Array.from({ length: rows }, (_, i) => shuffled[i % shuffled.length]);

  for (let rowIndex = 0; rowIndex < rows; rowIndex++) {
    const rowStart = rowIndex * ROW_LENGTH;

    const word = wordsForRows[rowIndex];     // ✅ different per row (until bank runs out)
    const letters = word.split("");

    let missingIndices = [];
    while (missingIndices.length < MISSING_COUNT) {
      const i = Math.floor(Math.random() * letters.length);
      if (!missingIndices.includes(i)) missingIndices.push(i);
    }

    for (let i = 0; i < ROW_LENGTH; i++) {
      const cell = gridCells[rowStart + i];
      if (!cell) continue;

      if (missingIndices.includes(i)) {
        cell.textContent = "";
        cell.setAttribute("data-expected", letters[i]);
        allExpectedLetters.push(letters[i]);
      } else {
        cell.textContent = letters[i];
        cell.removeAttribute("data-expected");
      }
    }
  }

  allExpectedLetters.sort(() => Math.random() - 0.5);

  const blocksContainer =
    document.querySelector(".blocks-row") ||
    document.querySelector(".blocks") ||
    document.querySelector("#div1");

  if (blocksContainer) {
    blocksContainer.innerHTML = "";

    allExpectedLetters.forEach((letter, idx) => {
      const block = document.createElement("div");
      block.textContent = letter;
      block.classList.add("block");
      block.draggable = true;
      block.id = `gen-block-${idx}`;

      if (typeof dragstartHandler === "function") {
        block.addEventListener("dragstart", dragstartHandler);
      }

      blocksContainer.appendChild(block);
    });
  }
});
