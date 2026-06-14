document.addEventListener('DOMContentLoaded', () => {
    window.onpageshow = function (event) {
        if (event.persisted || performance.getEntriesByType("navigation")[0].type === 'back_forward') {
            location.reload();
        }
    };

    function autoGrowTextarea(textarea) {
        textarea.style.height = 'auto';
        textarea.style.height = `${textarea.scrollHeight}px`;
    }

    const textarea = document.querySelector('textarea');
    if (textarea) {
        textarea.empty = true;
        textarea.addEventListener('input', () => autoGrowTextarea(textarea));
        autoGrowTextarea(textarea);
    }

    // Initialize PrismJS for Markdown-generated blocks
    const codeBlocks = document.querySelectorAll('pre');
    if (codeBlocks.length > 0) {
        codeBlocks.forEach((pre) => {
            pre.classList.add('line-numbers');
        });
        Prism.highlightAll();
    }
});