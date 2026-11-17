// Savepoint store desk.

// Helpers

const $ = (id) => document.getElementById(id);

let games = [];
let publishers = [];
let genres = [];
let customers = [];
let activeTab = "dashboard";
let gameRequest = 0;

async function api(method, url, body) {
  const options = { method, headers: {} };
  if (body !== undefined) {
    options.headers["Content-Type"] = "application/json";
    options.body = JSON.stringify(body);
  }
  let response;
  try {
    response = await fetch(url, options);
  } catch {
    setConnection(false);
    throw new Error("Cannot reach the store. Check that the app is running.");
  }
  setConnection(response.status < 500);
  const data = await response.json().catch(() => ({}));
  if (!response.ok)
    throw new Error(data.error || `Request failed (${response.status})`);
  return data;
}

// Database text must be escaped before it goes into an HTML template.
function esc(value) {
  return String(value ?? "").replace(
    /[&<>"']/g,
    (ch) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        ch
      ],
  );
}

const money = (n) => "$" + Number(n).toFixed(2);

let toastTimer;
function toast(message, isError = false) {
  const formError = document.querySelector("dialog[open] .form-error");
  if (isError && formError) {
    formError.textContent = message;
    formError.hidden = false;
  }
  const box = $("toast");
  box.textContent = message;
  box.className = "show" + (isError ? " error" : "");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => (box.className = ""), 3500);
}

async function run(action) {
  try {
    await action();
  } catch (error) {
    toast(error.message, true);
  }
}

function fillTable(bodyId, rows, emptyText) {
  const columns = $(bodyId).closest("table").querySelectorAll("th").length;
  $(bodyId).innerHTML = rows.length
    ? rows.join("")
    : `<tr><td class="empty" colspan="${columns}">${emptyText}</td></tr>`;
}

const editDeleteButtons = (name, id) => `
  <td class="actions-cell">
    <button class="small" data-action="edit-${name}" data-id="${id}">Edit</button>
    <button class="small danger" data-action="delete-${name}" data-id="${id}">Delete</button>
  </td>`;

const formData = (form) => Object.fromEntries(new FormData(form));

// Tabs

const loaders = {
  dashboard: loadDashboard,
  games: loadGames,
  publishers: loadPublishers,
  genres: loadGenres,
  customers: loadCustomers,
  orders: loadOrders,
};

const pages = {
  dashboard: [
    "01",
    "Overview",
    "A good day to play.",
    "Your catalogue, customers and sales. All in one place.",
  ],
  games: [
    "02",
    "Games",
    "The good stuff.",
    "Find a title, check the shelf, or bring in something new.",
  ],
  publishers: [
    "03",
    "Publishers",
    "Behind the games.",
    "Manage the publishers connected to your catalogue.",
  ],
  genres: [
    "04",
    "Genres",
    "Pick your adventure.",
    "Keep your games organised by the way people play.",
  ],
  customers: [
    "05",
    "Customers",
    "Your regulars.",
    "Contact details and order history, close at hand.",
  ],
  orders: [
    "06",
    "Orders",
    "Good games, going places.",
    "Record a sale, follow its progress, and keep stock in sync.",
  ],
};

function setConnection(online) {
  $("connectionStatus").className =
    "connection-status " + (online ? "online" : "offline");
  $("connectionText").textContent = online
    ? "Store connected"
    : "Connection unavailable";
  if (online) {
    $("lastSynced").textContent =
      "LAST SYNC / " +
      new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  }
}

async function showTab(name) {
  if (!pages[name]) return;
  activeTab = name;
  const [number, label, title, description] = pages[name];
  $("pageTitle").textContent = title;
  $("pageDescription").textContent = description;
  $("pageEyebrow").textContent = `${number} / STORE ${label.toUpperCase()}`;
  $("pageIndex").textContent = number;
  $("breadcrumbPage").textContent = label.toUpperCase();
  document.title = `${label} / Savepoint`;
  document.querySelectorAll("#tabs button").forEach((button) => {
    const selected = button.dataset.tab === name;
    button.classList.toggle("active", selected);
    if (selected) button.setAttribute("aria-current", "page");
    else button.removeAttribute("aria-current");
  });
  document.querySelectorAll(".tab").forEach((section) => {
    section.classList.toggle("active", section.id === name);
  });
  await run(loaders[name]);
}

$("tabs").addEventListener("click", (event) => {
  const button = event.target.closest("button[data-tab]");
  if (button) showTab(button.dataset.tab);
});

document.querySelector(".brand").addEventListener("click", (event) => {
  event.preventDefault();
  showTab("dashboard");
});

// Dashboard

async function loadDashboard() {
  const stats = await api("GET", "/api/stats");
  $("statGames").textContent = stats.counts.games;
  $("statCustomers").textContent = stats.counts.customers;
  $("statOrders").textContent = stats.counts.orders;
  $("statRevenue").textContent = money(stats.counts.revenue);
  $("lowStockNote").textContent =
    `Titles with ${stats.low_stock_limit} or fewer copies on the shelf.`;
  $("lowStockCount").textContent = stats.low_stock.length;

  const largestRevenue = Math.max(
    1,
    ...stats.top_sellers.map((game) => Number(game.revenue)),
  );
  fillTable(
    "topSellersBody",
    stats.top_sellers.map(
      (game, index) => `
    <tr>
      <td><div class="game-cell"><span class="rank">${String(index + 1).padStart(2, "0")}</span>
        <div><strong>${esc(game.title)}</strong><span class="subtext">${esc(game.platform)}</span></div></div></td>
      <td class="num">${game.units_sold}</td>
      <td class="num revenue-cell">${money(game.revenue)}
        <div class="bar-track" aria-hidden="true"><span class="bar-fill" style="width:${(Number(game.revenue) / largestRevenue) * 100}%"></span></div></td>
    </tr>`,
    ),
    "Completed orders will appear here.",
  );

  fillTable(
    "lowStockBody",
    stats.low_stock.map(
      (game) => `
    <tr><td><strong>${esc(game.title)}</strong><span class="subtext">${esc(game.platform)}</span></td>
      <td class="num">${stockBadge(game.stock)}</td></tr>`,
    ),
    "Everything is well stocked.",
  );
}

function stockBadge(stock) {
  if (stock === 0) return `<span class="badge out">Out of stock</span>`;
  if (stock <= 5) return `<span class="badge low">${stock}</span>`;
  return `<span class="stock-ok">${stock}</span>`;
}

// Games

async function loadGames() {
  [publishers, genres] = await Promise.all([
    api("GET", "/api/publishers"),
    api("GET", "/api/genres"),
  ]);
  fillSelect(
    $("gameGenreFilter"),
    genres,
    "genre_id",
    (g) => g.name,
    "All genres",
  );
  fillSelect(
    $("gamePublisherFilter"),
    publishers,
    "publisher_id",
    (p) => p.name,
    "All publishers",
  );
  await refreshGames();
}

function fillSelect(select, items, idField, label, firstOption) {
  const current = select.value;
  select.innerHTML =
    (firstOption ? `<option value="">${firstOption}</option>` : "") +
    items
      .map(
        (item) =>
          `<option value="${item[idField]}">${esc(label(item))}</option>`,
      )
      .join("");
  select.value = current;
  if (select.selectedIndex === -1) select.selectedIndex = 0;
}

async function refreshGames() {
  const request = ++gameRequest;
  const params = new URLSearchParams();
  if ($("gameSearch").value.trim())
    params.set("search", $("gameSearch").value.trim());
  if ($("gameGenreFilter").value)
    params.set("genre_id", $("gameGenreFilter").value);
  if ($("gamePublisherFilter").value)
    params.set("publisher_id", $("gamePublisherFilter").value);

  const result = await api("GET", "/api/games?" + params);
  // A slower search response must not overwrite a newer one.
  if (request !== gameRequest) return;
  games = result;
  $("gamesCount").textContent =
    `${games.length} ${games.length === 1 ? "title" : "titles"}`;
  fillTable(
    "gamesBody",
    games.map(
      (g) => `
    <tr>
      <td><div class="game-cell">${gameTile(g)}<div><strong>${esc(g.title)}</strong><span class="subtext">SP-${String(g.game_id).padStart(3, "0")}</span></div></div></td>
      <td>${esc(g.publisher_name)}</td>
      <td>${esc(g.platform)}</td>
      <td>${esc(g.genres)}</td>
      <td class="num">${money(g.price)}</td>
      <td class="num">${stockBadge(g.stock)}</td>
      <td class="nowrap">${esc(g.release_date || "")}</td>
      ${editDeleteButtons("game", g.game_id)}
    </tr>`,
    ),
    "No games match.",
  );
}

let searchTimer;
$("gameSearch").addEventListener("input", () => {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(() => run(refreshGames), 160);
});
$("gameGenreFilter").addEventListener("change", () => run(refreshGames));
$("gamePublisherFilter").addEventListener("change", () => run(refreshGames));

function gameTile(game) {
  const platformClass =
    {
      "PlayStation 5": "playstation",
      "Nintendo Switch": "switch",
      "Xbox Series X": "xbox",
    }[game.platform] || "pc";
  const initials = game.title
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((word) => word[0])
    .join("");
  return `<span class="game-tile ${platformClass}" aria-hidden="true">${esc(initials)}</span>`;
}

function openDialog(id) {
  const dialog = $(id);
  const error = dialog.querySelector(".form-error");
  if (error) error.hidden = true;
  if (!dialog.open) dialog.showModal();
}

function openGameForm(game) {
  const form = $("gameForm");
  form.reset();
  $("gameFormTitle").textContent = game ? "Edit game" : "Add game";
  fillSelect(form.publisher_id, publishers, "publisher_id", (p) => p.name);
  $("gameGenreChecks").innerHTML = genres
    .map(
      (g) => `
    <label><input type="checkbox" value="${g.genre_id}"> ${esc(g.name)}</label>`,
    )
    .join("");

  form.game_id.value = game ? game.game_id : "";
  if (game) {
    form.title.value = game.title;
    form.publisher_id.value = game.publisher_id;
    form.platform.value = game.platform;
    form.price.value = game.price;
    form.stock.value = game.stock;
    form.release_date.value = game.release_date || "";
    $("gameGenreChecks")
      .querySelectorAll("input")
      .forEach((box) => {
        box.checked = game.genre_ids.includes(Number(box.value));
      });
  }
  openDialog("gameDialog");
}

$("addGameBtn").addEventListener("click", () => openGameForm(null));

// Publishers

async function loadPublishers() {
  publishers = await api("GET", "/api/publishers");
  fillTable(
    "publishersBody",
    publishers.map(
      (p) => `
    <tr>
      <td>${esc(p.name)}</td>
      <td>${esc(p.country)}</td>
      <td>${esc(p.website)}</td>
      <td class="num">${p.game_count}</td>
      ${editDeleteButtons("publisher", p.publisher_id)}
    </tr>`,
    ),
    "No publishers yet.",
  );
}

function openPublisherForm(publisher) {
  const form = $("publisherForm");
  form.reset();
  $("publisherFormTitle").textContent = publisher
    ? "Edit publisher"
    : "Add publisher";
  form.publisher_id.value = publisher ? publisher.publisher_id : "";
  if (publisher) {
    form.name.value = publisher.name;
    form.country.value = publisher.country || "";
    form.website.value = publisher.website || "";
  }
  openDialog("publisherDialog");
}

$("addPublisherBtn").addEventListener("click", () => openPublisherForm(null));

// Genres

async function loadGenres() {
  genres = await api("GET", "/api/genres");
  fillTable(
    "genresBody",
    genres.map(
      (g) => `
    <tr>
      <td>${esc(g.name)}</td>
      <td class="num">${g.game_count}</td>
      ${editDeleteButtons("genre", g.genre_id)}
    </tr>`,
    ),
    "No genres yet.",
  );
}

function openGenreForm(genre) {
  const form = $("genreForm");
  form.reset();
  $("genreFormTitle").textContent = genre ? "Edit genre" : "Add genre";
  form.genre_id.value = genre ? genre.genre_id : "";
  if (genre) form.name.value = genre.name;
  openDialog("genreDialog");
}

$("addGenreBtn").addEventListener("click", () => openGenreForm(null));

// Customers

async function loadCustomers() {
  customers = await api("GET", "/api/customers");
  fillTable(
    "customersBody",
    customers.map(
      (c) => `
    <tr>
      <td>${esc(c.first_name)} ${esc(c.last_name)}</td>
      <td>${esc(c.email)}</td>
      <td>${esc(c.phone)}</td>
      <td class="num">${c.order_count}</td>
      ${editDeleteButtons("customer", c.customer_id)}
    </tr>`,
    ),
    "No customers yet.",
  );
}

function openCustomerForm(customer) {
  const form = $("customerForm");
  form.reset();
  $("customerFormTitle").textContent = customer
    ? "Edit customer"
    : "Add customer";
  form.customer_id.value = customer ? customer.customer_id : "";
  if (customer) {
    form.first_name.value = customer.first_name;
    form.last_name.value = customer.last_name;
    form.email.value = customer.email;
    form.phone.value = customer.phone || "";
  }
  openDialog("customerDialog");
}

$("addCustomerBtn").addEventListener("click", () => openCustomerForm(null));

function bindSaveForm(
  name,
  resource,
  reload,
  collect = (form) => formData(form),
) {
  const form = $(`${name}Form`);
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    run(async () => {
      const submit = form.querySelector('[type="submit"]');
      if (submit.disabled) return;
      submit.disabled = true;
      try {
        const body = collect(form);
        const id = body[`${name}_id`];
        delete body[`${name}_id`];
        await api(
          id ? "PUT" : "POST",
          `/api/${resource}${id ? `/${id}` : ""}`,
          body,
        );
        $(`${name}Dialog`).close();
        toast(`${name[0].toUpperCase() + name.slice(1)} saved`);
        await reload();
      } finally {
        submit.disabled = false;
      }
    });
  });
}

bindSaveForm("game", "games", refreshGames, (form) => {
  const data = formData(form);
  return {
    ...data,
    publisher_id: Number(data.publisher_id),
    stock: Number(data.stock),
    release_date: data.release_date || null,
    genre_ids: [...$("gameGenreChecks").querySelectorAll("input:checked")].map(
      (box) => Number(box.value),
    ),
  };
});
bindSaveForm("publisher", "publishers", loadPublishers);
bindSaveForm("genre", "genres", loadGenres);
bindSaveForm("customer", "customers", loadCustomers);

// Orders

async function loadOrders() {
  const orders = await api("GET", "/api/orders");
  fillTable(
    "ordersBody",
    orders.map(
      (o) => `
    <tr>
      <td>#${o.order_id}</td>
      <td>${esc(o.customer_name)}</td>
      <td class="nowrap">${esc(o.order_date)}</td>
      <td><span class="badge ${o.status}">${o.status}</span></td>
      <td class="num">${o.item_count}</td>
      <td class="num">${money(o.total)}</td>
      <td class="actions-cell">
        <button class="small" data-action="view-order" data-id="${o.order_id}">View</button>
        ${
          o.status === "PENDING"
            ? `
          <button class="small" data-action="complete-order" data-id="${o.order_id}">Complete</button>
          <button class="small" data-action="cancel-order" data-id="${o.order_id}">Cancel</button>`
            : ""
        }
        <button class="small danger" data-action="delete-order" data-id="${o.order_id}">Delete</button>
      </td>
    </tr>`,
    ),
    "No orders yet.",
  );
}

async function viewOrder(id) {
  const order = await api("GET", `/api/orders/${id}`);
  $("orderDetailTitle").textContent = `Order #${order.order_id}`;
  $("orderDetailInfo").innerHTML =
    `${esc(order.customer_name)} &middot; ${esc(order.order_date)} &middot; ` +
    `<span class="badge ${order.status}">${order.status}</span>`;
  fillTable(
    "orderDetailBody",
    order.items.map(
      (item) => `
    <tr>
      <td>${esc(item.title)}</td><td>${esc(item.platform)}</td>
      <td class="num">${item.quantity}</td>
      <td class="num">${money(item.unit_price)}</td>
      <td class="num">${money(item.line_total)}</td>
    </tr>`,
    ),
    "This order has no items.",
  );
  $("orderDetailTotal").textContent = money(order.total);
  openDialog("orderDetailDialog");
}

async function openOrderForm() {
  [customers, games] = await Promise.all([
    api("GET", "/api/customers"),
    api("GET", "/api/games"),
  ]);
  if (!customers.length) throw new Error("Add a customer first.");
  if (!games.some((game) => game.stock > 0))
    throw new Error("Add stock to a game before placing an order.");
  $("orderForm").reset();
  fillSelect(
    $("orderForm").customer_id,
    customers,
    "customer_id",
    (c) => `${c.first_name} ${c.last_name} (${c.email})`,
  );
  $("orderItems").innerHTML = "";
  addOrderItemRow();
  openDialog("orderDialog");
}

function addOrderItemRow() {
  const inStock = games.filter((g) => g.stock > 0);
  const row = document.createElement("div");
  row.className = "order-item";
  row.innerHTML = `
    <select class="item-game" aria-label="Game" required>
      ${inStock
        .map(
          (g) => `<option value="${g.game_id}">
        ${esc(g.title)} (${esc(g.platform)}) - ${money(g.price)}, ${g.stock} in stock</option>`,
        )
        .join("")}
    </select>
    <input class="item-qty" aria-label="Quantity" type="number" min="1" step="1" value="1" required>
    <button type="button" class="small danger remove-item">Remove</button>`;
  $("orderItems").appendChild(row);
  updateOrderTotal();
}

function updateOrderTotal() {
  let total = 0;
  $("orderItems")
    .querySelectorAll(".order-item")
    .forEach((row) => {
      const game = games.find(
        (g) => g.game_id === Number(row.querySelector(".item-game").value),
      );
      if (game)
        total += game.price * Number(row.querySelector(".item-qty").value || 0);
    });
  $("orderFormTotal").textContent = money(total);
}

$("addOrderBtn").addEventListener("click", () => run(openOrderForm));
$("quickOrderBtn").addEventListener("click", () => run(openOrderForm));
$("addOrderItemBtn").addEventListener("click", addOrderItemRow);
$("orderItems").addEventListener("input", updateOrderTotal);
$("orderItems").addEventListener("click", (event) => {
  if (event.target.classList.contains("remove-item")) {
    event.target.closest(".order-item").remove();
    updateOrderTotal();
  }
});

$("orderForm").addEventListener("submit", (event) => {
  event.preventDefault();
  run(async () => {
    const items = [...$("orderItems").querySelectorAll(".order-item")].map(
      (row) => ({
        game_id: Number(row.querySelector(".item-game").value),
        quantity: Number(row.querySelector(".item-qty").value),
      }),
    );
    if (!items.length) throw new Error("Add at least one game to the order.");
    await api("POST", "/api/orders", {
      customer_id: Number(event.target.customer_id.value),
      items,
    });
    $("orderDialog").close();
    toast("Order placed");
    await loaders[activeTab]();
  });
});

async function setOrderStatus(id, status) {
  await api("PUT", `/api/orders/${id}`, { status });
  toast(`Order #${id} is now ${status}`);
  await loadOrders();
}

// One click handler for all table buttons

async function remove(what, url, reload) {
  if (!confirm(`Delete this ${what}?`)) return;
  const result = await api("DELETE", url);
  toast(result.message);
  await reload();
}

const actions = {
  "edit-game": (id) => openGameForm(games.find((g) => g.game_id === id)),
  "delete-game": (id) => remove("game", `/api/games/${id}`, refreshGames),
  "edit-publisher": (id) =>
    openPublisherForm(publishers.find((p) => p.publisher_id === id)),
  "delete-publisher": (id) =>
    remove("publisher", `/api/publishers/${id}`, loadPublishers),
  "edit-genre": (id) => openGenreForm(genres.find((g) => g.genre_id === id)),
  "delete-genre": (id) => remove("genre", `/api/genres/${id}`, loadGenres),
  "edit-customer": (id) =>
    openCustomerForm(customers.find((c) => c.customer_id === id)),
  "delete-customer": (id) =>
    remove("customer", `/api/customers/${id}`, loadCustomers),
  "view-order": viewOrder,
  "complete-order": (id) => setOrderStatus(id, "COMPLETED"),
  "cancel-order": (id) => setOrderStatus(id, "CANCELLED"),
  "delete-order": (id) => remove("order", `/api/orders/${id}`, loadOrders),
};

document.addEventListener("click", (event) => {
  const button = event.target.closest("button");
  if (!button) return;
  if (button.dataset.go) showTab(button.dataset.go);
  const action = actions[button.dataset.action];
  if (action) run(() => action(Number(button.dataset.id)));
  if ("close" in button.dataset) button.closest("dialog").close();
});

// Start

document.querySelectorAll("dialog form").forEach((form) => {
  const error = document.createElement("p");
  error.className = "form-error";
  error.setAttribute("role", "alert");
  error.hidden = true;
  form.querySelector(".actions").before(error);
});
const today = new Date();
$("today").dateTime = today.toISOString();
$("today").textContent = today.toLocaleDateString(undefined, {
  day: "2-digit",
  month: "short",
  year: "numeric",
});
showTab("dashboard");
