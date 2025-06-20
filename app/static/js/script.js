// REGISTRO DO SERVICE WORKER (PWA)
if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/static/sw.js')
        .then(reg => console.log('Service Worker: Registrado com sucesso!', reg))
        .catch(err => console.log('Service Worker: Falha no registro.', err));
}

function verificarPermissaoNotificacao() {
    const alerta = document.getElementById('alerta-notificacao');
    if (!alerta) {
        if (Notification.permission === "granted") {
            iniciarVerificadorDeNotificacoes();
        }
        return;
    }

    const textoAlerta = document.getElementById('alerta-notificacao-texto');
    const btnAtivar = document.getElementById('btn-ativar-notificacoes');

    if (!("Notification" in window)) {
        textoAlerta.innerHTML = '<i class="bi bi-x-circle-fill me-2"></i> Este navegador não suporta notificações.';
        btnAtivar.style.display = 'none';
        alerta.classList.remove('alert-info', 'alert-danger');
        alerta.classList.add('alert-warning');
        alerta.style.display = 'flex';
        return;
    }

    function atualizarUI(permission) {
        if (permission === "granted") {
            alerta.style.display = 'none';
            iniciarVerificadorDeNotificacoes();
        } else if (permission === "denied") {
            alerta.classList.remove('alert-info');
            alerta.classList.add('alert-danger');
            textoAlerta.innerHTML = '<i class="bi bi-bell-slash-fill me-2"></i> As notificações estão bloqueadas. Para ativá-las, mude as configurações do seu navegador.';
            btnAtivar.style.display = 'none';
            alerta.style.display = 'flex';
        } else { // 'default'
            alerta.classList.remove('alert-danger');
            alerta.classList.add('alert-info');
            textoAlerta.innerHTML = '<i class="bi bi-bell-fill me-2"></i> Para receber alertas em tempo real, ative as notificações do navegador.';
            btnAtivar.style.display = 'block';
            alerta.style.display = 'flex';
        }
    }

    btnAtivar.addEventListener('click', () => {
        Notification.requestPermission().then(permission => {
            atualizarUI(permission); 
            if (permission === "granted") {
                new Notification("Obrigado por ativar!", {
                    body: "Você agora receberá notificações importantes do sistema.",
                    icon: "/static/images/icon-192x192.png"
                });
            }
        });
    });

    atualizarUI(Notification.permission);
}


let lastCheckTimestamp = new Date().toISOString();
let notificationInterval = null;

function verificarNovasNotificacoes() {
    fetch(`/api/novas-notificacoes?since=${lastCheckTimestamp}`)
        .then(response => response.json())
        .then(notificacoes => {
            if (notificacoes.length > 0) {
                notificacoes.forEach(notif => {
                    const notification = new Notification(notif.title, {
                        body: notif.body,
                        icon: '/static/images/icon-192x192.png'
                    });
                    notification.onclick = function() {
                        window.focus();
                        window.location.href = '/minhas-tarefas';
                    };
                });
                if (window.calendar) {
                    window.calendar.refetchEvents();
                }
            }
            lastCheckTimestamp = new Date().toISOString();
        })
        .catch(err => console.error("Erro ao buscar notificações:", err));
}

function iniciarVerificadorDeNotificacoes() {
    if (Notification.permission === "granted" && !notificationInterval) {
        console.log("Iniciando verificador de notificações...");
        verificarNovasNotificacoes(); 
        notificationInterval = setInterval(verificarNovasNotificacoes, 30000);
    }
}


document.addEventListener('DOMContentLoaded', function() {
    
    verificarPermissaoNotificacao();
    
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
        const currentTheme = localStorage.getItem('theme') || 'light';
        const sunIcon = 'bi-sun-fill';
        const moonIcon = 'bi-moon-stars-fill';
        if (currentTheme === 'dark') {
            document.documentElement.setAttribute('data-bs-theme', 'dark');
            if (themeToggle.querySelector('i')) themeToggle.querySelector('i').classList.replace(sunIcon, moonIcon);
        } else {
            document.documentElement.setAttribute('data-bs-theme', 'light');
            if (themeToggle.querySelector('i')) themeToggle.querySelector('i').classList.replace(moonIcon, sunIcon);
        }
        themeToggle.addEventListener('click', function() {
            const newTheme = document.documentElement.getAttribute('data-bs-theme') === 'dark' ? 'light' : 'dark';
            document.documentElement.setAttribute('data-bs-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            if (themeToggle.querySelector('i')) {
                if (newTheme === 'dark') {
                    themeToggle.querySelector('i').classList.replace(sunIcon, moonIcon);
                } else {
                    themeToggle.querySelector('i').classList.replace(moonIcon, sunIcon);
                }
            }
        });
    }

    const faqSearch = document.getElementById('faq-search');
    if (faqSearch) {
        faqSearch.addEventListener('keyup', function() {
            const searchTerm = this.value.toLowerCase();
            const faqItems = document.querySelectorAll('.faq-item');

            faqItems.forEach(function(item) {
                const questionText = item.querySelector('.accordion-button').textContent.toLowerCase();
                const answerText = item.querySelector('.accordion-body').textContent.toLowerCase();
                
                if (questionText.includes(searchTerm) || answerText.includes(searchTerm)) {
                    item.style.display = 'block';
                } else {
                    item.style.display = 'none';
                }
            });
        });
    }
    
    const chartCanvas = document.getElementById('labChart');
    if (chartCanvas) {
        try {
            const labels = JSON.parse(chartCanvas.dataset.labels || '[]');
            const values = JSON.parse(chartCanvas.dataset.values || '[]');
            
            if (labels.length > 0) {
                const ctx = chartCanvas.getContext('2d');
                new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: labels,
                        datasets: [{
                            label: 'Nº de Agendamentos',
                            data: values,
                            backgroundColor: 'rgba(13, 110, 253, 0.7)',
                            borderColor: 'rgba(13, 110, 253, 1)',
                            borderWidth: 1
                        }]
                    },
                    options: {
                        scales: {
                            y: {
                                beginAtZero: true,
                                ticks: {
                                    stepSize: 1
                                }
                            }
                        },
                        responsive: true,
                        maintainAspectRatio: false
                    }
                });
            }
        } catch (e) {
            console.error("Erro ao processar dados do gráfico:", e);
        }
    }

    var calendarEl = document.getElementById('calendar');
    if (calendarEl) {
        
        var modalAgendamentoEl = document.getElementById('modalAgendamento');
        var modalAgendamento = new bootstrap.Modal(modalAgendamentoEl);
        var formAgendamento = document.getElementById('formAgendamento');
        const mainContainer = document.getElementById('main-container');
        const userRole = mainContainer ? mainContainer.dataset.userRole : null;
        const currentUserId = mainContainer ? parseInt(mainContainer.dataset.userId) : null;
        let retainedData = null;

        const dataInput = document.getElementById('data');
        const secaoAtribuicao = document.getElementById('secao-atribuicao');
        const radioAtribuirUser = document.getElementById('atribuir_user');
        const radioAtribuirGrupo = document.getElementById('atribuir_group');
        const blocoUser = document.getElementById('bloco_atribuicao_user');
        const blocoGrupo = document.getElementById('bloco_atribuicao_grupo');
        const secaoManterDados = document.getElementById('secao-manter-dados');

        const filtroForm = document.getElementById('filtroForm');
        const filtroTexto = document.getElementById('filtro-texto');
        const filtroLab = document.getElementById('filtro-lab');
        const filtroStatus = document.getElementById('filtro-status');
        const btnLimparFiltros = document.getElementById('btnLimparFiltros');
        const btnExportar = document.getElementById('btnExportar');

        const btnSalvar = document.getElementById('btnSalvar');
        const btnSalvarAlteracoes = document.getElementById('btnSalvarAlteracoes');
        const btnExcluir = document.getElementById('btnExcluir');
        
        const Toast = Swal.mixin({
            toast: true,
            position: 'top-end',
            showConfirmButton: false,
            timer: 3000,
            timerProgressBar: true,
            didOpen: (toast) => {
                toast.addEventListener('mouseenter', Swal.stopTimer)
                toast.addEventListener('mouseleave', Swal.resumeTimer)
            }
        });

        modalAgendamentoEl.addEventListener('hidden.bs.modal', function () {
            formAgendamento.reset();
        });

        if (radioAtribuirUser) {
            radioAtribuirUser.addEventListener('change', function() { if (this.checked) {
                blocoUser.style.display = 'block';
                blocoGrupo.style.display = 'none';
            }});
        }
        if (radioAtribuirGrupo) {
            radioAtribuirGrupo.addEventListener('change', function() { if (this.checked) {
                blocoUser.style.display = 'none';
                blocoGrupo.style.display = 'block';
            }});
        }

        const savedView = localStorage.getItem('fullcalendar_view') || 'dayGridMonth';
        const savedDate = localStorage.getItem('fullcalendar_date') || new Date().toISOString();

        var calendar = new FullCalendar.Calendar(calendarEl, {
            initialView: savedView,
            initialDate: savedDate,
            headerToolbar: {
                left: 'prev,next today',
                center: 'title',
                right: 'dayGridMonth,timeGridWeek,timeGridDay'
            },
            locale: 'pt-br',
            buttonText: { today: 'Hoje', month: 'Mês', week: 'Semana', day: 'Dia' },
            dayMaxEvents: true, 
            moreLinkClassNames: ['fc-more-link-badge'],
            moreLinkContent: function(args) {
                return `+${args.num}`;
            },
            
            eventSources: [
                { id: 'agendamentos', url: `/api/agendamentos` },
                { id: 'feriados', url: '/api/feriados' },
                { id: 'recessos', url: '/api/recessos' }
            ],
            
            datesSet: function(dateInfo) {
                localStorage.setItem('fullcalendar_view', dateInfo.view.type);
                localStorage.setItem('fullcalendar_date', dateInfo.view.currentStart.toISOString());
            },

            dateClick: function(info) {
                const eventosDoDia = calendar.getEvents().filter(e => e.startStr === info.dateStr);
                const eventoDeFundo = eventosDoDia.find(e => e.display === 'background');
                if (eventoDeFundo) {
                    let tipoBloqueio = eventoDeFundo.source.id === 'feriados' ? 'feriado' : 'recesso';
                    Swal.fire({ icon: 'warning', title: 'Dia não disponível', text: `Não é possível agendar durante o ${tipoBloqueio} de ${eventoDeFundo.title}.`});
                    return;
                }
                
                formAgendamento.reset();
                document.getElementById('agendamento_id').value = '';
                document.getElementById('modalLabel').textContent = 'Novo Agendamento';
                dataInput.value = info.dateStr;
                dataInput.readOnly = true;
                
                const campos = [document.getElementById('titulo'), dataInput, document.getElementById('laboratorio'), document.getElementById('horario')];
                campos.forEach(campo => campo.disabled = false);

                if (retainedData) {
                    document.getElementById('titulo').value = retainedData.titulo;
                    document.getElementById('laboratorio').value = retainedData.laboratorio;
                    document.getElementById('horario').value = retainedData.horario;
                    if (userRole === 'Coordenador') {
                        if (retainedData.tipo_atribuicao === 'user') {
                            radioAtribuirUser.checked = true;
                            document.querySelector('#bloco_atribuicao_user select').value = retainedData.atribuido_id;
                        } else if (retainedData.tipo_atribuicao === 'group') {
                            radioAtribuirGrupo.checked = true;
                            document.querySelector('#bloco_atribuicao_grupo select').value = retainedData.atribuido_id;
                        }
                    }
                    retainedData = null; 
                }
                
                document.getElementById('infoSolicitante').style.display = 'none';
                document.getElementById('infoAtribuicao').style.display = 'none';
                document.getElementById('btnAprovar').style.display = 'none';
                document.getElementById('btnRejeitar').style.display = 'none';
                btnSalvarAlteracoes.style.display = 'none';
                btnExcluir.style.display = 'none';
                btnSalvar.style.display = 'block';
                secaoManterDados.style.display = 'block';
                
                if (userRole === 'Coordenador') {
                    secaoAtribuicao.style.display = 'block';
                    if (radioAtribuirUser.checked) {
                        radioAtribuirUser.dispatchEvent(new Event('change'));
                    } else {
                        radioAtribuirGrupo.dispatchEvent(new Event('change'));
                    }
                } else {
                    secaoAtribuicao.style.display = 'none';
                }
                
                modalAgendamento.show();
            },

            eventClick: function(info) {
                if (info.event.display === 'background') { return; }
                formAgendamento.reset();
                const props = info.event.extendedProps;
                
                document.getElementById('agendamento_id').value = info.event.id;
                document.getElementById('modalLabel').textContent = 'Detalhes do Agendamento';
                document.getElementById('titulo').value = info.event.title;
                dataInput.value = info.event.start.toISOString().split('T')[0];
                dataInput.readOnly = true;
                document.getElementById('laboratorio').value = props.laboratorio_id;
                document.getElementById('horario').value = props.horario_bloco;
                document.getElementById('solicitanteNome').textContent = props.solicitante;
                document.getElementById('atribuidoNome').textContent = props.atribuido_a;
                document.getElementById('infoSolicitante').style.display = 'block';
                document.getElementById('infoAtribuicao').style.display = 'block';
                secaoAtribuicao.style.display = 'none';
                secaoManterDados.style.display = 'none';
                btnSalvar.style.display = 'none';
                document.getElementById('btnAprovar').style.display = 'none';
                document.getElementById('btnRejeitar').style.display = 'none';
                btnSalvarAlteracoes.style.display = 'none';
                btnExcluir.style.display = 'none';
                
                const podeEditar = (currentUserId === props.solicitante_id || userRole === 'Coordenador');
                const campos = [document.getElementById('titulo'), document.getElementById('laboratorio'), document.getElementById('horario')];
                campos.forEach(campo => campo.disabled = !podeEditar);

                if (podeEditar) {
                    btnSalvarAlteracoes.style.display = 'block';
                    btnExcluir.style.display = 'block';
                }

                if (userRole === 'Coordenador' && props.status === 'Pendente') {
                    document.getElementById('btnAprovar').style.display = 'block';
                    document.getElementById('btnRejeitar').style.display = 'block';
                } 
                
                modalAgendamento.show();
            }
        });
        
        window.calendar = calendar;
        calendar.render();
        
        function atualizarLinkExportacao() {
            if (!btnExportar) return;
            const params = new URLSearchParams();
            if (filtroTexto.value) params.append('texto', filtroTexto.value);
            if (filtroLab.value) params.append('lab', filtroLab.value);
            if (filtroStatus.value) params.append('status', filtroStatus.value);
            btnExportar.href = `/relatorio/exportar?${params.toString()}`;
        }

        if (filtroForm) {
            atualizarLinkExportacao();
            filtroForm.addEventListener('submit', function(e) {
                e.preventDefault();
                let agendamentosSource = calendar.getEventSourceById('agendamentos');
                if (agendamentosSource) { agendamentosSource.remove(); }
                const params = new URLSearchParams();
                if (filtroTexto.value) params.append('texto', filtroTexto.value);
                if (filtroLab.value) params.append('lab', filtroLab.value);
                if (filtroStatus.value) params.append('status', filtroStatus.value);
                calendar.addEventSource({ id: 'agendamentos', url: `/api/agendamentos?${params.toString()}` });
                atualizarLinkExportacao();
            });

            btnLimparFiltros.addEventListener('click', function() {
                filtroForm.reset();
                filtroForm.dispatchEvent(new Event('submit'));
            });
        }

        btnSalvar.addEventListener('click', function() {
            const formData = new FormData(formAgendamento);
            const manterDadosCheck = document.getElementById('manterDados');
            if (manterDadosCheck.checked) {
                retainedData = {
                    titulo: formData.get('titulo'),
                    laboratorio: formData.get('laboratorio'),
                    horario: formData.get('horario'),
                    tipo_atribuicao: formData.get('tipo_atribuicao'),
                    atribuido_id: formData.get('tipo_atribuicao') === 'user' ? formData.get('atribuido_user_id') : formData.get('atribuido_grupo_id')
                };
            } else {
                retainedData = null;
            }
            manterDadosCheck.checked = false;
            fetch('/agendamento/novo', { method: 'POST', body: formData })
                .then(response => response.json())
                .then(data => {
                    if (data.success === false) {
                        Toast.fire({ icon: 'error', title: data.message });
                    } else if (data.success === true) {
                        Toast.fire({ icon: 'success', title: data.message });
                        calendar.refetchEvents();
                        if (!retainedData) {
                            modalAgendamento.hide();
                        }
                    }
                });
        });

        btnSalvarAlteracoes.addEventListener('click', function() {
            const id = document.getElementById('agendamento_id').value;
            if (!id) return;
            const formData = new FormData(formAgendamento);
            fetch(`/agendamento/editar/${id}`, { method: 'POST', body: formData })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        modalAgendamento.hide();
                        Toast.fire({ icon: 'success', title: data.message });
                        calendar.refetchEvents();
                    } else {
                        Swal.fire('Erro!', data.message || 'Não foi possível salvar as alterações.', 'error');
                    }
                });
        });

        btnExcluir.addEventListener('click', function() {
            const id = document.getElementById('agendamento_id').value;
            if (!id) return;
            Swal.fire({
                title: 'Tem certeza?',
                text: "Você não poderá reverter esta ação!",
                icon: 'warning',
                showCancelButton: true,
                confirmButtonColor: '#d33',
                cancelButtonColor: '#3085d6',
                confirmButtonText: 'Sim, excluir!',
                cancelButtonText: 'Cancelar'
            }).then((result) => {
                if (result.isConfirmed) {
                    fetch(`/agendamento/deletar/${id}`, { method: 'POST' })
                        .then(response => response.json())
                        .then(data => {
                            if (data.success) {
                                modalAgendamento.hide();
                                Toast.fire({ icon: 'success', title: data.message });
                                calendar.refetchEvents();
                            } else {
                                Swal.fire('Erro!', data.message || 'Não foi possível excluir o agendamento.', 'error');
                            }
                        });
                }
            });
        });

        document.getElementById('btnAprovar').addEventListener('click', function() {
            const id = document.getElementById('agendamento_id').value;
            fetch(`/agendamento/aprovar/${id}`, { method: 'POST' }).then(response => response.json()).then(data => {
                if (data.success) {
                    modalAgendamento.hide();
                    Swal.fire('Aprovado!', data.message, 'success');
                    calendar.refetchEvents();
                }
            });
        });

        document.getElementById('btnRejeitar').addEventListener('click', function() {
            const id = document.getElementById('agendamento_id').value;
            fetch(`/agendamento/rejeitar/${id}`, { method: 'POST' }).then(response => response.json()).then(data => {
                if (data.success) {
                    modalAgendamento.hide();
                    Swal.fire('Rejeitado!', data.message, 'warning');
                    calendar.refetchEvents();
                }
            });
        });
    }

    const chatForm = document.getElementById('chat-form');
    if (chatForm) {
        const chatWindow = document.getElementById('chat-window');
        const chatInput = document.getElementById('chat-input');
        chatForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const userQuestion = chatInput.value.trim();
            if (userQuestion === '') return;
            chatWindow.innerHTML += `<div class="d-flex flex-row justify-content-end mb-4 user-message"><div class="p-3 me-3 border" style="border-radius: 15px;"><p class="small mb-0">${userQuestion}</p></div></div>`;
            chatInput.value = '';
            chatWindow.scrollTop = chatWindow.scrollHeight;
            const thinkingId = 'thinking-' + Date.now();
            chatWindow.innerHTML += `<div class="d-flex flex-row justify-content-start mb-4 ai-message" id="${thinkingId}"><div class="p-3 ms-3" style="border-radius: 15px; background-color: rgba(52, 58, 64, 0.1);"><p class="small mb-0"><i>Pensando...</i></p></div></div>`;
            chatWindow.scrollTop = chatWindow.scrollHeight;
            fetch('/api/ajuda-chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question: userQuestion })
            })
            .then(response => response.json())
            .then(data => {
                const thinkingIndicator = document.getElementById(thinkingId);
                if (thinkingIndicator) {
                    thinkingIndicator.remove();
                }
                chatWindow.innerHTML += `<div class="d-flex flex-row justify-content-start mb-4 ai-message"><div class="p-3 ms-3" style="border-radius: 15px; background-color: rgba(52, 58, 64, 0.1);"><p class="small mb-0">${data.answer}</p></div></div>`;
                chatWindow.scrollTop = chatWindow.scrollHeight;
            })
            .catch(error => {
                const thinkingIndicator = document.getElementById(thinkingId);
                if (thinkingIndicator) {
                    thinkingIndicator.remove();
                }
                console.error("Erro no chat:", error);
                chatWindow.innerHTML += `<div class="d-flex flex-row justify-content-start mb-4 ai-message"><div class="p-3 ms-3 bg-danger text-white" style="border-radius: 15px;"><p class="small mb-0">Desculpe, não consegui obter uma resposta. Verifique o console ou os logs do servidor.</p></div></div>`;
                chatWindow.scrollTop = chatWindow.scrollHeight;
            });
        });
    }
});