// Initialize Flatpickr

Promise.all([initializeTransactions()]),then(() => { document.dispatchEvent(new Event('pageContentLoaded')); })

function initializeTransactions() {
    document.addEventListener('DOMContentLoaded', function () {
        flatpickr(".date-picker", {
            dateFormat: "Y-m-d",
            theme: "dark"
        });
    });

    // Color Transaction Amounts
    document.addEventListener('DOMContentLoaded', function () {
        document.querySelectorAll('.transaction-item .amount').forEach(function (amountElement) {
            const amountText = amountElement.textContent;
            const amountValue = parseFloat(amountText.replace(/[+$]/, '')); // Remove $ and +
            if (amountValue < 0) {
                amountElement.classList.add('negative');
            } else {
                amountElement.classList.add('positive');
            }
        });
    });


    // Search Functionality
    const searchInput = document.getElementById('search-input');
    const categoryItems = document.querySelectorAll(".transaction-item");
    const nothingFound = document.getElementById("nothingFound");

    searchInput.addEventListener("input", function () {
        const term = this.value.toLowerCase();
        let visibleCount = 0;

        categoryItems.forEach(item => {
            const nameEl = item.querySelector(".description");
            const descEl = item.querySelector(".amount");
            if (!nameEl || !descEl) return;

            const name = nameEl.textContent.toLowerCase();
            const description = descEl.textContent.toLowerCase();
            const match = name.includes(term) || description.includes(term);

            if (match) {
                item.classList.remove("hidden");
                visibleCount++;
            } else {
                item.classList.add("hidden");
            }
        });

        if (visibleCount === 0) {
            nothingFound.classList.add("show");
        } else {
            nothingFound.classList.remove("show");
        }
    });
    return true;
}

// Transaction Modal
$(document).ready(function () {
    $('.transaction-item').on('click', function () {
        const date = $(this).data('date');
        const description = $(this).data('description');
        const amount = $(this).data('amount');
        const category = $(this).data('category');
        $('#modal-date').text(date);
        $('#modal-description').text(description);
        $('#modal-amount').text(amount);
        $('#modal-category').text(category);
        $('#transactionModal').modal('show');
    });
});
