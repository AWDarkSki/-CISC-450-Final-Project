// Add event listeners to filter inputs; triggers filtering whenever any of them change or are updated
document.getElementById('search-bar').addEventListener('input', filterProducts);document.getElementById('search-bar').addEventListener('input', filterProducts);
document.getElementById('category-filter').addEventListener('change', filterProducts);
document.getElementById('size-filter').addEventListener('change', filterProducts);
document.getElementById('convention-filter').addEventListener('change', filterProducts);

// Function to fetch and display products based on current filter values
function filterProducts() {
    const category = document.getElementById('category-filter').value;
    const size = document.getElementById('size-filter').value;
    const search = document.getElementById('search-bar').value;
    const convention = document.getElementById('convention-filter').value;

    // Send filter data to the server and get matching product list
    fetch(`/data?category=${category}&size=${size}&search=${encodeURIComponent(search)}&convention=${encodeURIComponent(convention)}`)
        .then(response => response.json())
        .then(data => {
            displayProducts(data);  // Render filtered product data
        });
}

// Render product data into the table
function displayProducts(data) {
    const table = document.getElementById('data-table');
    table.innerHTML = '';   // Clear any previous results

    data.forEach(product => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td><img src="${product.image_url}" alt="${product.name}" width="50"></td>
            <td><a href="#" onclick="showProductDetail(${product.product_id}, '${escapeHtml(product.name)}', '${escapeHtml(product.image_url)}', '${escapeHtml(product.description)}', ${product.price}, '${escapeHtml(product.category)}', '${escapeHtml(product.size)}', ${product.stock_quantity})">${escapeHtml(product.name)}</a></td>
            <td>$${product.price.toFixed(2)}</td>
            <td><button onclick="addToWishlist(${product.product_id})">Add to Wishlist</button></td>
        `;
        table.appendChild(tr);  // Add the new row to the table
    });
}

// Show product details in a modal with additional convention info
function showProductDetail(id, name, image, description, price, category, size, stock) {
    document.getElementById('detail-name').textContent = name;
    document.getElementById('detail-image').src = image;
    document.getElementById('detail-description').textContent = description;
    document.getElementById('detail-price').textContent = price;
    document.getElementById('detail-category').textContent = category;
    document.getElementById('detail-size').textContent = size;
    document.getElementById('detail-stock').textContent = stock;

    // Fetch and display list of conventions where this product is available
    fetch(`/product/${id}/conventions`)
        .then(response => response.json())
        .then(conventions => {
            const display = conventions.length ? conventions.join(', ') : 'None listed';
            document.getElementById('detail-conventions').textContent = display;
        });
    // Show modal
    document.getElementById('product-detail').style.display = 'block';
    document.getElementById('modal-overlay').style.display = 'block';
}

// Close the product detail modal
function closeDetail() {
    document.getElementById('product-detail').style.display = 'none';
    document.getElementById('modal-overlay').style.display = 'none';
}

// Add a product to the wishlist using a POST request
function addToWishlist(productId) {
    fetch(`/wishlist/add/${productId}`, { method: 'POST' })
        .then(() => alert('Added to wishlist!'));
}

// Load convention filter options from the server and populate the dropdown
function loadConventions() {
    fetch('/conventions')
        .then(response => response.json())
        .then(conventions => {
            const select = document.getElementById('convention-filter');
            conventions.forEach(name => {
                const option = document.createElement('option');
                option.value = name;
                option.textContent = name;
                select.appendChild(option);
            });
        });
}

// Prevent XSS by escaping injected HTML strings
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Close modal if clicking outside of it
window.addEventListener('click', (event) => {
    const modal = document.getElementById('product-detail');
    const overlay = document.getElementById('modal-overlay');
    if (event.target === overlay) {
        closeDetail();
    }
});

// Initialize
window.addEventListener('DOMContentLoaded', () => {
    loadConventions();
    filterProducts(); // load initial product list
});
