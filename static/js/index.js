document.getElementById('search-bar').addEventListener('input', filterProducts);
document.getElementById('category-filter').addEventListener('change', filterProducts);
document.getElementById('size-filter').addEventListener('change', filterProducts);

function filterProducts() {
    const category = document.getElementById('category-filter').value;
    const size = document.getElementById('size-filter').value;
    const search = document.getElementById('search-bar').value;

    fetch(`/data?category=${category}&size=${size}&search=${search}`)
        .then(response => response.json())
        .then(data => {
            displayProducts(data);
        });
}

function displayProducts(data) {
    const table = document.getElementById('data-table');
    table.innerHTML = '';

    data.forEach(product => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td><img src="${product.image_url}" alt="${product.name}" width="50"></td>
            <td><a href="#" onclick="showProductDetail(${product.product_id}, '${product.name}', '${product.image_url}', '${product.description}', ${product.price}, '${product.category}', '${product.size}', ${product.stock_quantity})">${product.name}</a></td>
            <td>${product.price}</td>
            <td><button onclick="addToWishlist(${product.product_id})">Add to Wishlist</button></td>
        `;
        table.appendChild(tr);
    });
}


function viewProduct(productId) {
    fetch(`/product/${productId}`)
        .then(response => response.json())
        .then(product => {
            if (product.error) return;

            document.getElementById('product-detail').style.display = 'block';
            document.getElementById('detail-name').textContent = product.name;
            document.getElementById('detail-image').src = product.image_url;
            document.getElementById('detail-image').alt = product.name;
            document.getElementById('detail-description').textContent = product.description;
            document.getElementById('detail-price').textContent = product.price;
            document.getElementById('detail-category').textContent = product.category;
            document.getElementById('detail-size').textContent = product.size;
            document.getElementById('detail-stock').textContent = product.stock_quantity;
        });
}

function closeDetail() {
    document.getElementById('product-detail').style.display = 'none';
}

function showProductDetail(id, name, image, description, price, category, size, stock) {
    document.getElementById('detail-name').textContent = name;
    document.getElementById('detail-image').src = image;
    document.getElementById('detail-description').textContent = description;
    document.getElementById('detail-price').textContent = price;
    document.getElementById('detail-category').textContent = category;
    document.getElementById('detail-size').textContent = size;
    document.getElementById('detail-stock').textContent = stock;

    // Fetch conventions for this product
    fetch(`/product/${id}/conventions`)
        .then(response => response.json())
        .then(conventions => {
            const display = conventions.length ? conventions.join(', ') : 'None listed';
            document.getElementById('detail-conventions').textContent = display;
        });

    document.getElementById('product-detail').style.display = 'block';
}

function closeDetail() {
    document.getElementById('product-detail').style.display = 'none';
}


function addToWishlist(productId) {
    fetch(`/wishlist/add/${productId}`, { method: 'POST' })
        .then(() => alert('Added to wishlist!')); // Optional: confirmation
}
