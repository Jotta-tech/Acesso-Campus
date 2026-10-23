import { useCallback, useEffect, useMemo, useState } from "react";
import { api } from "./api";
import StatusBadge from "./components/StatusBadge";
import PriorityBadge from "./components/PriorityBadge";
import Loading from "./components/Loading";
import EmptyState from "./components/EmptyState";
import ErrorMessage from "./components/ErrorMessage";
import Alert from "./components/Alert";
import PageHeader from "./components/PageHeader";
import StatCard from "./components/StatCard";
import BarList from "./components/BarList";
import FormField from "./components/FormField";
import "./App.css";

const categoryLabels = {
  rampa: "Rampas", elevador: "Elevadores", corredor: "Corredores",
  banheiro: "Banheiros acessíveis", sinalizacao: "Sinalização",
  digital: "Acessibilidade digital", outros: "Outros",
};
const statusLabels = { pendente: "Pendente", em_andamento: "Em andamento", resolvida: "Resolvida" };
const priorityLabels = { baixa: "Baixa", media: "Média", alta: "Alta" };
const initialForm = { titulo: "", descricao: "", categoria: "rampa", localizacao: "" };

function formatDate(value) {
  if (!value) return "—";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "—" : date.toLocaleDateString("pt-BR", { day: "2-digit", month: "short", year: "numeric" });
}

export default function App() {
  const [dashboard, setDashboard] = useState(null);
  const [results, setResults] = useState({ results: [], count: 0, next: null, previous: null });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [search, setSearch] = useState("");
  const [filters, setFilters] = useState({ status: "", prioridade: "", categoria: "" });
  const [page, setPage] = useState(1);
  const [showForm, setShowForm] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [form, setForm] = useState(initialForm);
  const [formError, setFormError] = useState("");
  const [admin, setAdmin] = useState(null);
  const [adminOpen, setAdminOpen] = useState(false);
  const [adminLogin, setAdminLogin] = useState({ username: "", password: "" });
  const [adminBusy, setAdminBusy] = useState(false);
  const [adminError, setAdminError] = useState("");
  const [selected, setSelected] = useState(null);
  const [editStatus, setEditStatus] = useState("pendente");
  const [editPriority, setEditPriority] = useState("media");
  const [saveBusy, setSaveBusy] = useState(false);
  const [detailError, setDetailError] = useState("");

  useEffect(() => {
    let alive = true;
    api.sessaoAdmin().then((session) => { if (alive) setAdmin(session); })
      .catch(() => { if (alive) setAdmin({ authenticated: false, can_manage: false }); });
    return () => { alive = false; };
  }, []);

  useEffect(() => {
    if (!selected) return undefined;
    const onKeyDown = (event) => { if (event.key === "Escape" && !saveBusy) setSelected(null); };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [selected, saveBusy]);

  function showDetails(item) {
    setSelected(item);
    setEditStatus(item.status);
    setEditPriority(item.prioridade);
    setDetailError("");
  }

  async function handleAdminLogin(event) {
    event.preventDefault();
    setAdminBusy(true);
    setAdminError("");
    try {
      const session = await api.entrarAdmin(adminLogin.username, adminLogin.password);
      setAdmin(session);
      setAdminLogin({ username: "", password: "" });
      setAdminOpen(false);
      setNotice(`Acesso administrativo liberado para ${session.username}.`);
    } catch (err) { setAdminError(err.message || "Falha na autenticação."); }
    finally { setAdminBusy(false); }
  }

  async function handleLogout() {
    setAdminBusy(true);
    setAdminError("");
    try {
      await api.sairAdmin();
      setAdmin({ authenticated: false, can_manage: false });
      setSelected(null);
      setNotice("Sessão administrativa encerrada.");
    } catch (err) { setAdminError(err.message || "Não foi possível sair."); }
    finally { setAdminBusy(false); }
  }

  async function saveDetails(event) {
    event.preventDefault();
    if (!selected || !admin?.can_manage) return;
    setSaveBusy(true);
    setDetailError("");
    try {
      await api.csrfAdmin();
      await api.atualizarOcorrencia(selected.id, { status: editStatus, prioridade: editPriority });
      setSelected(null);
      setNotice(`Ocorrência #${selected.id} atualizada com sucesso.`);
      await loadData();
    } catch (err) {
      if (/401|403/.test(err.message || "")) setAdmin({ authenticated: false, can_manage: false });
      setDetailError(err.message || "Não foi possível atualizar a ocorrência.");
    } finally { setSaveBusy(false); }
  }

  const loadData = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [dash, list] = await Promise.all([
        api.dashboard(),
        api.ocorrencias({ page, search, ...filters }),
      ]);
      setDashboard(dash);
      setResults({
        results: Array.isArray(list) ? list : (list.results || []),
        count: Array.isArray(list) ? list.length : (list.count ?? 0),
        next: Array.isArray(list) ? null : list.next,
        previous: Array.isArray(list) ? null : list.previous,
      });
    } catch (err) {
      setError(err.message || "Verifique se o servidor Django está em execução.");
    } finally {
      setLoading(false);
    }
  }, [page, search, filters]);

  useEffect(() => { loadData(); }, [loadData]);

  const totalPages = useMemo(() => Math.max(1, Math.ceil(results.count / 10)), [results.count]);
  const updateFilter = (key, value) => {
    setPage(1);
    setFilters((current) => ({ ...current, [key]: value }));
  };

  async function submitForm(event) {
    event.preventDefault();
    setSubmitting(true);
    setFormError("");
    setNotice("");
    try {
      await api.criarOcorrencia(form);
      setForm(initialForm);
      setShowForm(false);
      setPage(1);
      setNotice("Ocorrência registrada com sucesso.");
      await loadData();
    } catch (err) {
      setFormError(err.message || "Não foi possível registrar a ocorrência.");
    } finally {
      setSubmitting(false);
    }
  }

  const dashboardStatus = dashboard?.por_status || {};
  const dashboardCategory = dashboard?.por_categoria || {};
  const dashboardPriority = dashboard?.por_prioridade || {};

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <a className="brand" href="#" onClick={(event) => { event.preventDefault(); setPage(1); window.scrollTo({ top: 0, behavior: "smooth" }); }}>
          <span className="brand-mark">A</span><span>Acesso<span className="brand-light">Campus</span><small>ACESSIBILIDADE UNIVERSITÁRIA</small></span>
        </a>
        <div className="sidebar-label">ESPAÇO DE TRABALHO</div>
        <button className="nav-item active" onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}><span>▦</span> Visão geral</button>
        <button className="nav-item" onClick={() => document.getElementById("ocorrencias")?.scrollIntoView({ behavior: "smooth" })}><span>☷</span> Ocorrências</button>
        <button className={`nav-item ${adminOpen ? "active" : ""}`} onClick={() => { setAdminOpen((value) => !value); setAdminError(""); window.scrollTo({ top: 0, behavior: "smooth" }); }}><span>♙</span> Administração</button>
        <div className="sidebar-bottom"><div className="sidebar-help-icon">i</div><strong>Campus para todos</strong><p>Uma universidade mais acessível começa com a participação de todos.</p></div>
      </aside>

      <main className="main-content">
        <header className="topbar"><div className="breadcrumb">Acesso Campus <span>/</span> Visão geral</div><div className="topbar-tag"><span className="online-dot" /> Portal de acessibilidade</div></header>
        <div className="content-wrap">
          <PageHeader eyebrow="PAINEL DE ACESSIBILIDADE" title="Visão geral" description="Acompanhe relatos e ajude a construir um campus acessível para todos." action={<button className="button button-primary" onClick={() => { setShowForm((value) => !value); setFormError(""); }}><span>＋</span> Registrar ocorrência</button>} />

          {notice && <Alert type="success" onClose={() => setNotice("")}>{notice}</Alert>}
          <ErrorMessage message={error} onRetry={loadData} />

          {adminOpen && <section className="panel admin-panel" aria-label="Acesso administrativo">
            <div className="panel-heading"><div><p className="eyebrow">ÁREA RESTRITA</p><h2>Administração</h2><p>Somente usuários autorizados podem alterar ocorrências.</p></div><button type="button" className="icon-button" onClick={() => setAdminOpen(false)} aria-label="Fechar administração">×</button></div>
            <div className="admin-body">
              {adminError && <Alert type="error">{adminError}</Alert>}
              {admin?.can_manage ? <div className="admin-session"><p><strong>Conectado como {admin.username}</strong> · Você pode alterar status e prioridades na tela de detalhes.</p><button type="button" className="button button-secondary" disabled={adminBusy} onClick={handleLogout}>Sair</button></div>
                : <form className="admin-login" onSubmit={handleAdminLogin}>
                  <FormField label="Usuário administrador"><input autoComplete="username" required value={adminLogin.username} onChange={(e) => setAdminLogin({ ...adminLogin, username: e.target.value })} /></FormField>
                  <FormField label="Senha"><input type="password" autoComplete="current-password" required value={adminLogin.password} onChange={(e) => setAdminLogin({ ...adminLogin, password: e.target.value })} /></FormField>
                  <button className="button button-primary" disabled={adminBusy}>{adminBusy ? "Entrando..." : "Entrar"}</button>
                </form>}
            </div>
          </section>}

          <section className="stats-grid" aria-label="Indicadores">
            <StatCard label="Total de ocorrências" value={dashboard?.total ?? "—"} hint="Relatos registrados" icon="▤" />
            <StatCard label="Pendentes" value={dashboardStatus.pendente ?? "—"} hint="Aguardando análise" icon="◷" />
            <StatCard label="Em andamento" value={dashboardStatus.em_andamento ?? "—"} hint="Em processo de resolução" icon="↗" />
            <StatCard label="Resolvidas" value={dashboardStatus.resolvida ?? "—"} hint="Barreiras solucionadas" icon="✓" />
          </section>

          {showForm && <section className="panel form-panel" id="novo-relato">
            <div className="panel-heading"><div><p className="eyebrow">CONTRIBUA COM O CAMPUS</p><h2>Registrar ocorrência</h2><p>Descreva a barreira de acessibilidade encontrada.</p></div><button className="icon-button" onClick={() => setShowForm(false)} aria-label="Fechar formulário">×</button></div>
            {formError && <Alert type="error">{formError}</Alert>}
            <form onSubmit={submitForm} className="occurrence-form">
              <FormField label="Título"><input required minLength="5" maxLength="120" value={form.titulo} onChange={(e) => setForm({ ...form, titulo: e.target.value })} placeholder="Ex.: Rampa bloqueada na entrada" /></FormField>
              <FormField label="Categoria"><select value={form.categoria} onChange={(e) => setForm({ ...form, categoria: e.target.value })}>{Object.entries(categoryLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></FormField>
              <FormField label="Localização"><input required minLength="3" maxLength="150" value={form.localizacao} onChange={(e) => setForm({ ...form, localizacao: e.target.value })} placeholder="Bloco, andar ou local específico" /></FormField>
              <FormField label="Descrição"><textarea required minLength="10" maxLength="2000" rows="4" value={form.descricao} onChange={(e) => setForm({ ...form, descricao: e.target.value })} placeholder="Conte o que aconteceu e como isso dificulta o acesso..." /></FormField>
              <div className="form-footer"><p>O relato será registrado como pendente para avaliação.</p><button className="button button-primary" disabled={submitting}>{submitting ? "Enviando..." : "Enviar ocorrência"}</button></div>
            </form>
          </section>}

          <section className="analytics-grid">
            <BarList title="Ocorrências por status" labels={statusLabels} items={Object.entries(dashboardStatus).map(([key, value]) => ({ key, value }))} />
            <BarList title="Prioridade dos relatos" labels={priorityLabels} items={Object.entries(dashboardPriority).map(([key, value]) => ({ key, value }))} />
          </section>

          <section className="panel" id="ocorrencias">
            <div className="panel-heading list-heading"><div><p className="eyebrow">ACOMPANHAMENTO</p><h2>Ocorrências recentes</h2><p>Consulte os relatos registrados no campus.</p></div><span className="count-pill">{results.count} {results.count === 1 ? "registro" : "registros"}</span></div>
            <div className="filters">
              <div className="search-box"><span>⌕</span><input aria-label="Pesquisar ocorrências" placeholder="Buscar por título ou descrição..." value={search} onChange={(e) => { setSearch(e.target.value); setPage(1); }} /></div>
              <select aria-label="Filtrar por status" value={filters.status} onChange={(e) => updateFilter("status", e.target.value)}><option value="">Todos os status</option>{Object.entries(statusLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select>
              <select aria-label="Filtrar por prioridade" value={filters.prioridade} onChange={(e) => updateFilter("prioridade", e.target.value)}><option value="">Todas as prioridades</option>{Object.entries(priorityLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select>
              <select aria-label="Filtrar por categoria" value={filters.categoria} onChange={(e) => updateFilter("categoria", e.target.value)}><option value="">Todas as categorias</option>{Object.entries(categoryLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select>
            </div>
            {loading ? <Loading /> : results.results.length === 0 ? <EmptyState /> : <div className="table-wrap"><table className="occurrence-table"><thead><tr><th>OCORRÊNCIA</th><th>CATEGORIA</th><th>PRIORIDADE</th><th>STATUS</th><th>DATA</th><th>AÇÃO</th></tr></thead><tbody>{results.results.map((item) => <tr key={item.id}><td><button type="button" className="occurrence-link" onClick={() => showDetails(item)} aria-label={`Ver detalhes da ocorrência ${item.id}`}>#{item.id} · {item.titulo}</button><div className="occurrence-location">{item.localizacao}</div></td><td>{item.categoria_display || categoryLabels[item.categoria] || item.categoria}</td><td><PriorityBadge priority={item.prioridade} /></td><td><StatusBadge status={item.status} /></td><td>{formatDate(item.data_criacao)}</td><td><button type="button" className="button button-secondary details-button" onClick={() => showDetails(item)}>Ver detalhes</button></td></tr>)}</tbody></table></div>}
            <div className="pagination"><span>Página {page} de {totalPages}</span><div><button className="button button-secondary" disabled={page <= 1 || loading} onClick={() => setPage((value) => value - 1)}>Anterior</button><button className="button button-secondary" disabled={!results.next || loading} onClick={() => setPage((value) => value + 1)}>Próxima</button></div></div>
          </section>

          {selected && <div className="detail-backdrop" onMouseDown={(event) => { if (event.target === event.currentTarget && !saveBusy) setSelected(null); }}>
            <section role="dialog" aria-modal="true" aria-labelledby="detail-heading" className="detail-dialog">
              <div className="detail-head"><div><p className="eyebrow">RELATO #{selected.id}</p><h2 id="detail-heading">{selected.titulo}</h2><p>{selected.categoria_display || categoryLabels[selected.categoria] || selected.categoria}</p></div><button type="button" autoFocus className="icon-button" aria-label="Fechar detalhes" onClick={() => setSelected(null)} disabled={saveBusy}>×</button></div>
              <div className="detail-body">
                <div className="detail-badges"><StatusBadge status={selected.status} /><PriorityBadge priority={selected.prioridade} /></div>
                <h3>Localização</h3><p>{selected.localizacao}</p>
                <h3>Descrição</h3><p className="detail-description">{selected.descricao}</p>
                <h3>Registrado em</h3><p>{formatDate(selected.data_criacao)}</p>
                {admin?.can_manage && <form className="manage-form" onSubmit={saveDetails}>
                  <h3>Gerenciar ocorrência</h3>
                  {detailError && <Alert type="error">{detailError}</Alert>}
                  <div className="manage-fields"><FormField label="Status"><select value={editStatus} onChange={(e) => setEditStatus(e.target.value)}>{Object.entries(statusLabels).map(([value, label]) => <option value={value} key={value}>{label}</option>)}</select></FormField>
                    <FormField label="Prioridade"><select value={editPriority} onChange={(e) => setEditPriority(e.target.value)}>{Object.entries(priorityLabels).map(([value, label]) => <option value={value} key={value}>{label}</option>)}</select></FormField></div>
                  <button type="submit" className="button button-primary" disabled={saveBusy}>{saveBusy ? "Salvando..." : "Salvar alterações"}</button>
                </form>}
                {!admin?.can_manage && <p className="read-only-note">Para gerenciar este relato, entre na área Administração.</p>}
              </div>
            </section>
          </div>}

          <footer className="footer"><span>© {new Date().getFullYear()} Acesso Campus</span><span>Promovendo acessibilidade, uma ocorrência por vez.</span></footer>
        </div>
      </main>
    </div>
  );
}
