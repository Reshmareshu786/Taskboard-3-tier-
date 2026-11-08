const list = document.getElementById("list");
const err = document.getElementById("err");

async function api(path, opts = {}) {
  const r = await fetch("/api/" + path, {
    headers: { "Content-Type": "application/json" }, ...opts });
  if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
  return r.status === 204 ? null : r.json();
}

async function load() {
  try {
    const tasks = await api("tasks");
    err.textContent = "";
    list.innerHTML = "";
    tasks.forEach(t => {
      const li = document.createElement("li");
      if (t.done) li.className = "done";
      const span = document.createElement("span");
      span.textContent = t.title;
      span.onclick = async () => { await api(`tasks/${t.id}/toggle`, { method: "PUT" }); load(); };
      const del = document.createElement("button");
      del.textContent = "✕";
      del.onclick = async () => { await api(`tasks/${t.id}`, { method: "DELETE" }); load(); };
      li.append(span, del);
      list.append(li);
    });
  } catch (e) { err.textContent = "Error: " + e.message; }
}

document.getElementById("f").onsubmit = async e => {
  e.preventDefault();
  const input = document.getElementById("title");
  try {
    await api("tasks", { method: "POST", body: JSON.stringify({ title: input.value }) });
    input.value = "";
    load();
  } catch (e) { err.textContent = "Error: " + e.message; }
};

load();
