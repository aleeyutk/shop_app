// ==============================================================================
// NovaShop — Frontend Application Logic
// ==============================================================================

const state = {
  products: [],
  categories: [],
  cart: JSON.parse(localStorage.getItem('novashop_cart') || '[]'),
  currentUser: null,
  activeCategory: 'all',
  activeSort: 'featured',
  searchQuery: '',
  googleAuthAvailable: false,
};

// ------------------------------------------------------------------------------
// Initialization
// ------------------------------------------------------------------------------
document.addEventListener('DOMContentLoaded', async () => {
  initLucide();
  setupEventListeners();
  updateCartBadge();
  
  // Parallel initial fetches
  await Promise.all([
    fetchHealth(),
    fetchCurrentUser(),
    fetchCategories(),
    loadProducts(),
  ]);

  if (state.currentUser) {
    await syncCartFromServer();
  }

  // Periodic polling for real-time synchronization between Web & Mobile (every 2.5s)
  setInterval(() => {
    if (state.currentUser) {
      syncCartFromServer();
    }
  }, 2500);

  // Sync immediately when browser window regains focus
  window.addEventListener('focus', () => {
    if (state.currentUser) {
      syncCartFromServer();
    }
  });

  // Check URL query parameters for login status
  const urlParams = new URLSearchParams(window.location.search);
  if (urlParams.get('login') === 'success') {
    showToast('🎉 Successfully signed in with Google!', 'success');
    window.history.replaceState({}, document.title, window.location.pathname);
  }
});

function initLucide() {
  if (window.lucide) {
    window.lucide.createIcons();
  }
}

// ------------------------------------------------------------------------------
// API Calls & Data Fetching
// ------------------------------------------------------------------------------
async function fetchHealth() {
  try {
    const res = await fetch('/api/health');
    if (!res.ok) return;
    const data = await res.json();
    state.googleAuthAvailable = !!data.google_auth_configured;
    
    const engineText = document.getElementById('healthEngineText');
    if (engineText) {
      engineText.textContent = `${data.database_engine} ${data.mailgun_configured ? '• Mailgun' : ''}`;
    }
  } catch (err) {
    console.warn('Health check failed:', err);
  }
}

async function fetchCurrentUser() {
  try {
    const res = await fetch('/auth/me');
    if (res.ok) {
      state.currentUser = await res.json();
      renderAuthUser(state.currentUser);
      await syncCartFromServer();
    } else {
      state.currentUser = null;
      renderAuthGuest();
    }
  } catch (err) {
    state.currentUser = null;
    renderAuthGuest();
  }
}

async function syncCartFromServer() {
  if (!state.currentUser) return;
  try {
    const res = await fetch('/api/cart');
    if (!res.ok) return;
    const cartData = await res.json();
    state.cart = cartData.items.map(it => ({
      product: it.product,
      quantity: it.quantity,
    }));
    saveCart();
    updateCartBadge();
    const drawer = document.getElementById('cartDrawer');
    if (drawer && !drawer.classList.contains('hidden')) {
      renderCartDrawer();
    }
  } catch (err) {
    console.warn('Cart sync failed:', err);
  }
}

async function fetchCategories() {
  try {
    const res = await fetch('/api/categories');
    if (!res.ok) return;
    state.categories = await res.json();
    renderCategoryTabs(state.categories);
  } catch (err) {
    console.error('Error fetching categories:', err);
  }
}

async function loadProducts() {
  const grid = document.getElementById('productsGrid');
  grid.innerHTML = `
    <div class="col-span-full py-16 text-center text-slate-400">
      <i data-lucide="loader" class="w-8 h-8 animate-spin mx-auto text-brand-600"></i>
      <p class="mt-3 text-sm">Refreshing product catalog...</p>
    </div>
  `;
  initLucide();

  try {
    const params = new URLSearchParams();
    if (state.activeCategory && state.activeCategory !== 'all') {
      params.append('category', state.activeCategory);
    }
    if (state.searchQuery) {
      params.append('search', state.searchQuery);
    }
    if (state.activeSort) {
      params.append('sort', state.activeSort);
    }

    const res = await fetch(`/api/products?${params.toString()}`);
    if (!res.ok) throw new Error('Failed to load products');
    state.products = await res.json();
    renderProducts(state.products);
  } catch (err) {
    grid.innerHTML = `
      <div class="col-span-full py-16 text-center text-red-500">
        <i data-lucide="alert-circle" class="w-8 h-8 mx-auto mb-2"></i>
        <p class="font-semibold">Unable to load catalog</p>
        <p class="text-xs text-slate-500 mt-1">${err.message}</p>
      </div>
    `;
    initLucide();
  }
}

// ------------------------------------------------------------------------------
// Rendering Functions
// ------------------------------------------------------------------------------
function renderCategoryTabs(categories) {
  const container = document.getElementById('categoryTabs');
  const allBtn = container.querySelector('[data-category="all"]');
  container.innerHTML = '';
  container.appendChild(allBtn);

  categories.forEach(cat => {
    const btn = document.createElement('button');
    btn.dataset.category = cat.slug;
    btn.className = 'category-btn px-4 py-2 text-xs sm:text-sm font-semibold rounded-full transition shadow-sm';
    btn.innerHTML = `${cat.name} <span class="opacity-60 text-xs ml-1 font-normal">(${cat.product_count})</span>`;
    btn.addEventListener('click', () => {
      document.querySelectorAll('.category-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      state.activeCategory = cat.slug;
      loadProducts();
    });
    container.appendChild(btn);
  });

  allBtn.addEventListener('click', () => {
    document.querySelectorAll('.category-btn').forEach(b => b.classList.remove('active'));
    allBtn.classList.add('active');
    state.activeCategory = 'all';
    loadProducts();
  });
}

function renderProducts(products) {
  const grid = document.getElementById('productsGrid');
  if (products.length === 0) {
    grid.innerHTML = `
      <div class="col-span-full py-16 text-center text-slate-400">
        <i data-lucide="package-search" class="w-12 h-12 mx-auto text-slate-300 mb-3"></i>
        <h3 class="text-base font-semibold text-slate-700">No products found</h3>
        <p class="text-xs text-slate-500 mt-1">Try clearing your search query or choosing another category.</p>
      </div>
    `;
    initLucide();
    return;
  }

  grid.innerHTML = products.map(product => `
    <div class="product-card bg-white rounded-2xl border border-slate-200/80 overflow-hidden flex flex-col shadow-sm">
      <div class="relative aspect-square w-full overflow-hidden bg-slate-100 group">
        <img 
          src="${product.image_url}" 
          alt="${product.name}" 
          loading="lazy" 
          class="w-full h-full object-cover object-center group-hover:scale-105 transition-transform duration-300"
        />
        ${product.is_featured ? `
          <span class="absolute top-3 left-3 bg-brand-600/90 backdrop-blur-sm text-white text-[10px] font-bold uppercase tracking-wider px-2.5 py-1 rounded-full shadow-sm">
            Featured
          </span>
        ` : ''}
        <span class="absolute top-3 right-3 bg-slate-900/70 backdrop-blur-sm text-white text-[11px] font-medium px-2 py-0.5 rounded-full flex items-center gap-1">
          <i data-lucide="star" class="w-3 h-3 fill-amber-400 text-amber-400"></i> ${product.rating.toFixed(1)}
        </span>
      </div>

      <div class="p-5 flex-1 flex flex-col justify-between">
        <div>
          <h3 class="text-sm font-bold text-slate-900 line-clamp-1 hover:text-brand-600 transition" title="${product.name}">
            ${product.name}
          </h3>
          <p class="mt-1 text-xs text-slate-500 line-clamp-2 leading-relaxed">
            ${product.description}
          </p>
        </div>

        <div class="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between">
          <div>
            <span class="text-xs text-slate-400 font-medium">Price</span>
            <div class="text-lg font-extrabold text-slate-900">$${product.price.toFixed(2)}</div>
          </div>

          <button 
            onclick="handleAddToCart(${product.id})" 
            class="py-2 px-3.5 bg-slate-900 hover:bg-brand-600 active:scale-95 text-white text-xs font-semibold rounded-xl flex items-center gap-1.5 transition shadow-sm"
          >
            <i data-lucide="plus" class="w-3.5 h-3.5"></i>
            <span>Add</span>
          </button>
        </div>
      </div>
    </div>
  `).join('');

  initLucide();
}

function renderAuthGuest() {
  const container = document.getElementById('authContainer');
  container.innerHTML = `
    <div class="flex items-center gap-1.5">
      <button onclick="openLoginModal()" class="flex items-center gap-1.5 px-3 py-1.5 text-xs sm:text-sm font-semibold text-white bg-brand-600 hover:bg-brand-700 rounded-lg shadow-sm transition">
        <i data-lucide="log-in" class="w-3.5 h-3.5"></i>
        <span>Sign In</span>
      </button>
      <button onclick="handleQuickDemoLogin()" class="px-2.5 py-1.5 text-xs font-semibold text-amber-800 bg-amber-100 hover:bg-amber-200 border border-amber-300 rounded-lg transition" title="1-Click Demo Login">
        ⚡ Demo
      </button>
    </div>
  `;
  initLucide();
}

function renderAuthUser(user) {
  const container = document.getElementById('authContainer');
  const avatar = user.avatar_url || 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=100&q=80';
  
  container.innerHTML = `
    <div class="relative group">
      <button class="flex items-center gap-2 p-1 pl-2 pr-3 bg-slate-100 hover:bg-slate-200 rounded-full transition text-xs font-semibold text-slate-800">
        <img src="${avatar}" alt="${user.name}" class="w-6 h-6 rounded-full object-cover" />
        <span class="max-w-[90px] truncate hidden sm:inline">${user.name.split(' ')[0]}</span>
        <i data-lucide="chevron-down" class="w-3.5 h-3.5 text-slate-500"></i>
      </button>

      <!-- Dropdown -->
      <div class="absolute right-0 mt-2 w-48 bg-white border border-slate-200 rounded-xl shadow-xl py-2 hidden group-hover:block group-focus-within:block z-50">
        <div class="px-4 py-2 border-b border-slate-100">
          <p class="text-xs font-bold text-slate-900 truncate">${user.name}</p>
          <p class="text-[11px] text-slate-500 truncate">${user.email}</p>
        </div>
        <button onclick="openOrdersModal()" class="w-full text-left px-4 py-2 text-xs text-slate-700 hover:bg-slate-50 flex items-center gap-2">
          <i data-lucide="package" class="w-3.5 h-3.5"></i> My Orders
        </button>
        <button onclick="handleLogout()" class="w-full text-left px-4 py-2 text-xs text-red-600 hover:bg-red-50 flex items-center gap-2">
          <i data-lucide="log-out" class="w-3.5 h-3.5"></i> Sign Out
        </button>
      </div>
    </div>
  `;
  initLucide();
}

async function handleQuickDemoLogin() {
  try {
    const res = await fetch('/auth/mock-login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: 'Alex Rivera',
        email: 'alex.rivera@example.com',
        avatar_url: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=200&q=80',
      }),
    });
    if (res.ok) {
      state.currentUser = await res.json();
      renderAuthUser(state.currentUser);
      await syncCartFromServer();
      showToast('Logged in as demo user (Alex Rivera)', 'success');
    }
  } catch (err) {
    showToast('Demo login failed', 'error');
  }
}

async function handleLogout() {
  try {
    await fetch('/auth/logout', { method: 'POST' });
    state.currentUser = null;
    state.cart = [];
    saveCart();
    updateCartBadge();
    renderCartDrawer();
    renderAuthGuest();
    showToast('Signed out successfully', 'info');
  } catch (err) {
    console.error('Logout error:', err);
  }
}

// ------------------------------------------------------------------------------
// Cart Operations
// ------------------------------------------------------------------------------
async function handleAddToCart(productId) {
  const product = state.products.find(p => p.id === productId);
  if (!product) return;

  const existingIndex = state.cart.findIndex(item => item.product.id === productId);
  if (existingIndex > -1) {
    state.cart[existingIndex].quantity += 1;
  } else {
    state.cart.push({ product, quantity: 1 });
  }

  saveCart();
  updateCartBadge();
  showToast(`Added "${product.name}" to cart`, 'success');

  if (state.currentUser) {
    try {
      await fetch('/api/cart', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ product_id: productId, quantity: 1 }),
      });
      syncCartFromServer();
    } catch (err) {
      console.warn('Failed to sync added item with server:', err);
    }
  }
}

async function updateCartQuantity(productId, delta) {
  const index = state.cart.findIndex(item => item.product.id === productId);
  if (index === -1) return;

  const newQty = state.cart[index].quantity + delta;
  if (newQty <= 0) {
    state.cart.splice(index, 1);
  } else {
    state.cart[index].quantity = newQty;
  }

  saveCart();
  renderCartDrawer();
  updateCartBadge();

  if (state.currentUser) {
    try {
      if (newQty <= 0) {
        await fetch(`/api/cart/${productId}`, { method: 'DELETE' });
      } else {
        await fetch(`/api/cart/${productId}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ quantity: newQty }),
        });
      }
      syncCartFromServer();
    } catch (err) {
      console.warn('Failed to sync item quantity with server:', err);
    }
  }
}

async function removeFromCart(productId) {
  state.cart = state.cart.filter(item => item.product.id !== productId);
  saveCart();
  renderCartDrawer();
  updateCartBadge();

  if (state.currentUser) {
    try {
      await fetch(`/api/cart/${productId}`, { method: 'DELETE' });
      syncCartFromServer();
    } catch (err) {
      console.warn('Failed to sync item removal with server:', err);
    }
  }
}

function saveCart() {
  localStorage.setItem('novashop_cart', JSON.stringify(state.cart));
}

function updateCartBadge() {
  const totalCount = state.cart.reduce((sum, item) => sum + item.quantity, 0);
  const badge = document.getElementById('cartCountBadge');
  if (badge) {
    badge.textContent = totalCount;
  }
}

function calculateCartTotals() {
  const subtotal = state.cart.reduce((sum, item) => sum + item.product.price * item.quantity, 0);
  const shipping = subtotal >= 50 || subtotal === 0 ? 0 : 5.0;
  const total = subtotal + shipping;
  return { subtotal, shipping, total };
}

function renderCartDrawer() {
  const container = document.getElementById('cartItemsList');
  const subtotalEl = document.getElementById('cartSubtotal');
  const shippingEl = document.getElementById('cartShipping');
  const totalEl = document.getElementById('cartTotal');
  const checkoutBtn = document.getElementById('openCheckoutBtn');

  if (state.cart.length === 0) {
    container.innerHTML = `
      <div class="h-full flex flex-col items-center justify-center text-center p-6 text-slate-400">
        <i data-lucide="shopping-bag" class="w-16 h-16 text-slate-300 mb-4 stroke-1"></i>
        <h4 class="text-base font-semibold text-slate-700">Your cart is empty</h4>
        <p class="text-xs text-slate-500 mt-1 max-w-[200px]">Explore our catalog and add items to begin checkout.</p>
      </div>
    `;
    subtotalEl.textContent = '$0.00';
    shippingEl.textContent = 'Free';
    totalEl.textContent = '$0.00';
    checkoutBtn.disabled = true;
    initLucide();
    return;
  }

  checkoutBtn.disabled = false;
  container.innerHTML = state.cart.map(item => `
    <div class="flex items-center gap-3 p-3 bg-slate-50 rounded-xl border border-slate-200/60">
      <img src="${item.product.image_url}" alt="${item.product.name}" class="w-14 h-14 object-cover rounded-lg shrink-0" />
      <div class="flex-1 min-w-0">
        <h4 class="text-xs font-bold text-slate-900 truncate">${item.product.name}</h4>
        <p class="text-xs font-semibold text-brand-600 mt-0.5">$${item.product.price.toFixed(2)}</p>
        
        <div class="flex items-center gap-2 mt-2">
          <button onclick="updateCartQuantity(${item.product.id}, -1)" class="w-6 h-6 rounded bg-white border border-slate-300 flex items-center justify-center text-slate-600 hover:bg-slate-100 text-xs">
            -
          </button>
          <span class="text-xs font-bold text-slate-800 w-5 text-center">${item.quantity}</span>
          <button onclick="updateCartQuantity(${item.product.id}, 1)" class="w-6 h-6 rounded bg-white border border-slate-300 flex items-center justify-center text-slate-600 hover:bg-slate-100 text-xs">
            +
          </button>
        </div>
      </div>
      <button onclick="removeFromCart(${item.product.id})" class="p-1.5 text-slate-400 hover:text-red-500 rounded-lg hover:bg-red-50 transition" title="Remove">
        <i data-lucide="trash-2" class="w-4 h-4"></i>
      </button>
    </div>
  `).join('');

  const totals = calculateCartTotals();
  subtotalEl.textContent = `$${totals.subtotal.toFixed(2)}`;
  shippingEl.textContent = totals.shipping === 0 ? 'Free' : `$${totals.shipping.toFixed(2)}`;
  totalEl.textContent = `$${totals.total.toFixed(2)}`;

  initLucide();
}

// ------------------------------------------------------------------------------
// Checkout & Order Placement
// ------------------------------------------------------------------------------
function openCheckoutModal() {
  if (state.cart.length === 0) {
    showToast('Your cart is empty', 'warning');
    return;
  }

  // Close cart drawer
  closeCartDrawer();

  // Populate order summary
  const totals = calculateCartTotals();
  const totalItemCount = state.cart.reduce((sum, it) => sum + it.quantity, 0);

  document.getElementById('checkoutItemsCount').textContent = totalItemCount;
  document.getElementById('checkoutSubtotal').textContent = `$${totals.subtotal.toFixed(2)}`;
  document.getElementById('checkoutShipping').textContent = totals.shipping === 0 ? 'Free' : `$${totals.shipping.toFixed(2)}`;
  document.getElementById('checkoutTotal').textContent = `$${totals.total.toFixed(2)}`;

  // Autofill user details if logged in
  if (state.currentUser) {
    document.getElementById('custName').value = state.currentUser.name || '';
    document.getElementById('custEmail').value = state.currentUser.email || '';
  }

  document.getElementById('checkoutModal').classList.remove('hidden');
}

function closeCheckoutModal() {
  document.getElementById('checkoutModal').classList.add('hidden');
}

async function handleCheckoutSubmit(e) {
  e.preventDefault();
  const placeBtn = document.getElementById('placeOrderBtn');
  placeBtn.disabled = true;
  placeBtn.innerHTML = `
    <i data-lucide="loader" class="w-4 h-4 animate-spin"></i>
    <span>Processing & Sending Email...</span>
  `;
  initLucide();

  const checkoutPayload = {
    items: state.cart.map(item => ({
      product_id: item.product.id,
      quantity: item.quantity,
    })),
    customer_name: document.getElementById('custName').value.trim(),
    customer_email: document.getElementById('custEmail').value.trim(),
    customer_phone: document.getElementById('custPhone').value.trim() || null,
    shipping_address: document.getElementById('custAddress').value.trim(),
    city: document.getElementById('custCity').value.trim(),
    state: document.getElementById('custState').value.trim(),
    postal_code: document.getElementById('custZip').value.trim(),
    country: 'United States',
    payment_method: 'VISA •••• 4242',
  };

  try {
    const res = await fetch('/api/checkout', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(checkoutPayload),
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Checkout failed');
    }

    const order = await res.json();

    // Clear Cart
    state.cart = [];
    saveCart();
    updateCartBadge();
    renderCartDrawer();

    // Close checkout and show confirmation
    closeCheckoutModal();
    openConfirmationModal(order);
    showToast('Order confirmed! Confirmation email dispatched.', 'success');

  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    placeBtn.disabled = false;
    placeBtn.innerHTML = `
      <i data-lucide="lock" class="w-4 h-4"></i>
      <span>Pay & Place Order</span>
    `;
    initLucide();
  }
}

function openConfirmationModal(order) {
  document.getElementById('confirmOrderId').textContent = order.id;
  document.getElementById('confirmOrderTotal').textContent = `$${order.total_amount.toFixed(2)} ${order.currency}`;
  document.getElementById('confirmEmail').textContent = order.customer_email;
  document.getElementById('confirmationModal').classList.remove('hidden');
}

function closeConfirmationModal() {
  document.getElementById('confirmationModal').classList.add('hidden');
}

// ------------------------------------------------------------------------------
// Orders History Modal
// ------------------------------------------------------------------------------
async function openOrdersModal() {
  const modal = document.getElementById('ordersModal');
  const container = document.getElementById('ordersListContainer');
  modal.classList.remove('hidden');

  container.innerHTML = `
    <div class="py-12 text-center text-slate-400">
      <i data-lucide="loader" class="w-8 h-8 animate-spin mx-auto text-brand-600"></i>
      <p class="mt-2 text-xs">Fetching orders from database...</p>
    </div>
  `;
  initLucide();

  try {
    const res = await fetch('/api/orders');
    if (!res.ok) throw new Error('Could not load orders');
    const orders = await res.json();

    if (orders.length === 0) {
      container.innerHTML = `
        <div class="py-12 text-center text-slate-400">
          <i data-lucide="package-x" class="w-12 h-12 mx-auto text-slate-300 mb-2"></i>
          <p class="text-sm font-semibold text-slate-700">No orders found yet</p>
          <p class="text-xs text-slate-500 mt-0.5">Complete a checkout to see orders stored in the database.</p>
        </div>
      `;
      initLucide();
      return;
    }

    container.innerHTML = orders.map(order => `
      <div class="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-3">
        <div class="flex items-center justify-between">
          <div>
            <span class="text-xs font-mono font-bold text-slate-900">${order.id}</span>
            <span class="text-[11px] text-slate-500 block">${new Date(order.created_at).toLocaleDateString()} at ${new Date(order.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span>
          </div>
          <span class="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800">
            ${order.status}
          </span>
        </div>

        <div class="text-xs text-slate-600 space-y-1 border-t border-slate-200/60 pt-2">
          ${order.items.map(it => `
            <div class="flex justify-between">
              <span>${it.product_name} <strong class="text-slate-400">x${it.quantity}</strong></span>
              <span class="font-semibold text-slate-800">$${it.subtotal.toFixed(2)}</span>
            </div>
          `).join('')}
        </div>

        <div class="flex justify-between items-center border-t border-slate-200/60 pt-2 text-xs">
          <span class="text-slate-500">Recipient: ${order.customer_name} (${order.city}, ${order.state})</span>
          <span class="font-bold text-brand-700 text-sm">$${order.total_amount.toFixed(2)}</span>
        </div>
      </div>
    `).join('');

    initLucide();
  } catch (err) {
    container.innerHTML = `
      <div class="py-8 text-center text-red-500 text-xs">
        Failed to fetch orders: ${err.message}
      </div>
    `;
  }
}

function closeOrdersModal() {
  document.getElementById('ordersModal').classList.add('hidden');
}

// ------------------------------------------------------------------------------
// UI Drawer Handlers & Event Listeners
// ------------------------------------------------------------------------------
function openCartDrawer() {
  renderCartDrawer();
  document.getElementById('cartDrawer').classList.remove('hidden');
}

function closeCartDrawer() {
  document.getElementById('cartDrawer').classList.add('hidden');
}

function setupEventListeners() {
  // Cart Drawer
  document.getElementById('cartDrawerBtn').addEventListener('click', openCartDrawer);
  document.getElementById('closeCartBtn').addEventListener('click', closeCartDrawer);
  document.getElementById('cartBackdrop').addEventListener('click', closeCartDrawer);

  // Checkout Modal
  document.getElementById('openCheckoutBtn').addEventListener('click', openCheckoutModal);
  document.getElementById('closeCheckoutBtn').addEventListener('click', closeCheckoutModal);
  document.getElementById('checkoutForm').addEventListener('submit', handleCheckoutSubmit);

  // Confirmation Modal
  document.getElementById('closeConfirmBtn').addEventListener('click', closeConfirmationModal);
  document.getElementById('viewMyOrdersConfirmBtn').addEventListener('click', () => {
    closeConfirmationModal();
    openOrdersModal();
  });

  // Orders Modal
  document.getElementById('viewOrdersBtn').addEventListener('click', openOrdersModal);
  document.getElementById('closeOrdersBtn').addEventListener('click', closeOrdersModal);

  // Search Inputs (debounced)
  let searchTimeout;
  const handleSearch = (e) => {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
      state.searchQuery = e.target.value.trim();
      loadProducts();
    }, 300);
  };

  document.getElementById('searchInput').addEventListener('input', handleSearch);
  document.getElementById('mobileSearchInput').addEventListener('input', handleSearch);

  // Sort Dropdown
  document.getElementById('sortSelect').addEventListener('change', (e) => {
    state.activeSort = e.target.value;
    loadProducts();
  });
}

// ------------------------------------------------------------------------------
// Toast Notification Helper
// ------------------------------------------------------------------------------
function showToast(message, type = 'info') {
  const container = document.getElementById('toastContainer');
  const toast = document.createElement('div');
  
  const colors = {
    success: 'bg-emerald-600 text-white',
    error: 'bg-red-600 text-white',
    warning: 'bg-amber-500 text-white',
    info: 'bg-slate-900 text-white',
  };

  toast.className = `toast-enter flex items-center gap-2 px-4 py-3 rounded-xl shadow-lg text-xs font-medium pointer-events-auto ${colors[type] || colors.info}`;
  toast.innerHTML = `<span>${message}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transition = 'opacity 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

// ------------------------------------------------------------------------------
// Login Modal Handlers
// ------------------------------------------------------------------------------
function openLoginModal() {
  const modal = document.getElementById('loginModal');
  if (modal) {
    modal.classList.remove('hidden');
    initLucide();
  }
}

function closeLoginModal() {
  const modal = document.getElementById('loginModal');
  if (modal) {
    modal.classList.add('hidden');
  }
}

async function handleCustomEmailLogin(e) {
  e.preventDefault();
  const nameInput = document.getElementById('loginNameInput');
  const emailInput = document.getElementById('loginEmailInput');
  const btn = document.getElementById('customLoginBtn');
  
  const name = nameInput ? nameInput.value.trim() : '';
  const email = emailInput ? emailInput.value.trim() : '';
  if (!email || !name) return;

  btn.disabled = true;
  btn.innerHTML = `<i data-lucide="loader" class="w-4 h-4 animate-spin"></i><span>Signing in...</span>`;
  initLucide();

  try {
    const res = await fetch('/auth/mock-login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name,
        email,
        avatar_url: `https://ui-avatars.com/api/?name=${encodeURIComponent(name)}&background=0D8ABC&color=fff`,
      }),
    });
    if (!res.ok) throw new Error('Sign in failed');
    state.currentUser = await res.json();
    renderAuthUser(state.currentUser);
    await syncCartFromServer();
    closeLoginModal();
    showToast(`Welcome, ${state.currentUser.name}!`, 'success');
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<span>Continue with Account</span><i data-lucide="arrow-right" class="w-4 h-4"></i>`;
    initLucide();
  }
}

function handleGoogleAuthClick() {
  if (state.googleAuthAvailable) {
    window.location.href = '/auth/google/login';
  } else {
    showToast('Google OAuth is not configured on this instance. Please use Email Sign In or 1-Click Demo!', 'warning');
  }
}

// Expose handlers to global window for inline onclick handlers
window.handleAddToCart = handleAddToCart;
window.updateCartQuantity = updateCartQuantity;
window.removeFromCart = removeFromCart;
window.handleQuickDemoLogin = handleQuickDemoLogin;
window.handleLogout = handleLogout;
window.openOrdersModal = openOrdersModal;
window.openLoginModal = openLoginModal;
window.closeLoginModal = closeLoginModal;
window.handleCustomEmailLogin = handleCustomEmailLogin;
window.handleGoogleAuthClick = handleGoogleAuthClick;
