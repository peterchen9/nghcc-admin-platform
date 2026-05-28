const moduleNav = document.querySelector("#moduleNav");
const moduleGrid = document.querySelector("#moduleGrid");
const healthText = document.querySelector("#healthText");
const statusDot = document.querySelector("#statusDot");
const apiSignal = document.querySelector("#apiSignal");

async function loadHealth() {
  try {
    const response = await fetch("/api/health/");
    const data = await response.json();
    statusDot.classList.add("ok");
    healthText.textContent = `後端正常，資料庫狀態：${data.database}`;
    apiSignal.textContent = data.app;
  } catch (error) {
    statusDot.classList.add("error");
    healthText.textContent = "後端尚未連線，請檢查 Docker logs。";
  }
}

async function loadModules() {
  const response = await fetch("/api/modules/");
  const modules = await response.json();

  moduleNav.innerHTML = modules
    .map((item) => `<a class="nav-item" href="#${item.slug}">${item.name}</a>`)
    .join("");

  moduleGrid.innerHTML = modules
    .map(
      (item) => `
        <article class="module-card" id="${item.slug}">
          <h3>${item.icon} ${item.name}</h3>
          <p>${item.description}</p>
        </article>
      `
    )
    .join("");
}

loadHealth();
loadModules().catch(() => {
  moduleGrid.innerHTML = '<article class="module-card"><h3>模組讀取失敗</h3><p>請確認後端容器已啟動。</p></article>';
});

