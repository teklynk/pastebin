function autoGrowTextarea(textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = `${textarea.scrollHeight}px`;
}
document.addEventListener('DOMContentLoaded', () => {
    window.onpageshow = function (event) {
        if (event.persisted || performance.getEntriesByType("navigation")[0].type === 'back_forward') {
            location.reload();
        }
    };

    const textarea = document.querySelector('textarea');
    if (textarea) {
        textarea.empty = true;
        textarea.addEventListener('input', () => autoGrowTextarea(textarea));
        autoGrowTextarea(textarea);
    }
});