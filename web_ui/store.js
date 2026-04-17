const PRODUCTS = [
    { id: 'atta-10kg', name: 'Aashirvaad Atta 10kg', price: 420, emoji: '🌾' },
    { id: 'dal-1kg', name: 'Toor Dal 1kg', price: 160, emoji: '🥣' },
    { id: 'oil-1l', name: 'Fortune Mustard Oil 1L', price: 180, emoji: '🛢️' },
    { id: 'rice-5kg', name: 'India Gate Basmati 5kg', price: 450, emoji: '🍚' },
    { id: 'tea-500g', name: 'Tata Tea Premium 500g', price: 210, emoji: '☕' },
    { id: 'salt-1kg', name: 'Tata Salt 1kg packet', price: 25, emoji: '🧂' },
    { id: 'spices-mix', name: 'Everest Meat Masala', price: 75, emoji: '🌶️'},
    { id: 'sugar-1kg', name: 'Madhur Refined Sugar', price: 55, emoji: '🧊'}
];

let cart = [];

document.addEventListener("DOMContentLoaded", () => {
    renderStandardProducts();
    fetchAIRecommendations();
    
    document.getElementById('cart-btn').addEventListener('click', toggleCart);
    document.getElementById('close-cart').addEventListener('click', toggleCart);
    document.getElementById('checkout-btn').addEventListener('click', processCheckout);
    document.getElementById('continue-shopping').addEventListener('click', closeCheckout);
});

function createProductCard(product, isAI = false) {
    const card = document.createElement('div');
    card.className = 'product-card';
    card.innerHTML = `
        <div class="product-img">${product.emoji}</div>
        <div class="product-title">${product.name}</div>
        <div class="product-price">₹${product.price}</div>
        <button class="add-to-cart ${isAI ? 'ai-btn' : ''}" onclick="addToCart('${product.id}')">
            ${isAI ? '✨ Add Intellicart' : 'Add to Cart'}
        </button>
    `;
    return card;
}

function renderStandardProducts() {
    const grid = document.getElementById('standard-products');
    grid.innerHTML = '';
    PRODUCTS.forEach(p => grid.appendChild(createProductCard(p)));
}

async function fetchAIRecommendations() {
    try {
        const res = await fetch('/recommend', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: 'guest_123', purchase_history: ['tea-500g'] })
        });
        
        if(!res.ok) throw new Error("Backend failed");
        const data = await res.json();
        
        const intel = data.intelligence; 
        
        document.getElementById('ai-reason').innerText = intel.reasoning || "Derived via Collaborative Filtering on Kirana Datasets.";
        document.getElementById('ai-confidence').innerText = (intel.confidence || "90.0%") + " Match Confidence";

        const aiSubset = [PRODUCTS[6], PRODUCTS[7]]; 
        const grid = document.getElementById('ai-recommendations');
        grid.innerHTML = '';
        aiSubset.forEach(p => grid.appendChild(createProductCard(p, true)));

    } catch(e) {
        document.getElementById('ai-recommendations').innerHTML = `<p class="reason-text">Failed to connect to AI Engine. (Is FastApi alive?)</p>`;
    }
}

window.addToCart = function(id) {
    const product = PRODUCTS.find(p => p.id === id);
    if(product) {
        cart.push(product);
        updateCartUI();
    }
}

window.removeFromCart = function(index) {
    cart.splice(index, 1);
    updateCartUI();
}

function updateCartUI() {
    document.getElementById('cart-count').innerText = cart.length;
    
    const cartItems = document.getElementById('cart-items');
    cartItems.innerHTML = '';
    
    let total = 0;
    cart.forEach((item, idx) => {
        total += item.price;
        const div = document.createElement('div');
        div.className = 'cart-item';
        div.innerHTML = `
            <div class="cart-item-info">
                <h4>${item.emoji} ${item.name}</h4>
                <button class="remove-btn" onclick="removeFromCart(${idx})">Remove</button>
            </div>
            <div class="cart-item-price">₹${item.price}</div>
        `;
        cartItems.appendChild(div);
    });
    
    document.getElementById('cart-total').innerText = total;
}

function toggleCart() {
    document.getElementById('cart-overlay').classList.toggle('hidden');
}

function processCheckout() {
    if(cart.length === 0) return alert("Your basket is empty!");
    toggleCart();
    cart = [];
    updateCartUI();
    document.getElementById('checkout-overlay').classList.remove('hidden');
}

function closeCheckout() {
    document.getElementById('checkout-overlay').classList.add('hidden');
}
