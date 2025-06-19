document.addEventListener('DOMContentLoaded', function() {
    
    // Lógica do Modo Noturno (Dark Mode)
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

    // Lógica da Página de Ajuda/FAQ
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

    // Lógica do Gráfico do Dashboard
    const chartCanvas = document.getElementById('labChart');
    if (chartCanvas && typeof chartData !== 'undefined') {
        const labels = chartData.labels;
        const values = chartData.values;
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
                        y: { beginAtZero: true, ticks: { stepSize: 1 } }
                    },
                    responsive: true,
                    maintainAspectRatio: false
                }
            });
        }
    }

    // Lógica Específica da Página do Calendário
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
                document.getElementById('btnSalvarAlteracoes').style.display = 'none';
                document.getElementById('btnExcluir').style.display = 'none';
                document.getElementById('btnSalvar').style.display = 'block';
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
                document.getElementById('laboratorio').value = props.laboratorio_id;
                document.getElementById('horario').value = props.horario_bloco;

                document.getElementById('solicitanteNome').textContent = props.solicitante;
                document.getElementById('atribuidoNome').textContent = props.atribuido_a;
                document.getElementById('infoSolicitante').style.display = 'block';
                document.getElementById('infoAtribuicao').style.display = 'block';
                secaoAtribuicao.style.display = 'none';
                secaoManterDados.style.display = 'none';

                const podeEditar = (currentUserId === props.solicitante_id || userRole === 'Coordenador');
                const campos = [document.getElementById('titulo'), document.getElementById('laboratorio'), document.getElementById('horario')];
                campos.forEach(campo => campo.disabled = !podeEditar);
                dataInput.readOnly = true;

                document.getElementById('btnSalvar').style.display = 'none';
                document.getElementById('btnAprovar').style.display = 'none';
                document.getElementById('btnRejeitar').style.display = 'none';
                document.getElementById('btnSalvarAlteracoes').style.display = 'none';
                document.getElementById('btnExcluir').style.display = 'none';
                
                if (userRole === 'Coordenador' && props.status === 'Pendente') {
                    document.getElementById('btnAprovar').style.display = 'block';
                    document.getElementById('btnRejeitar').style.display = 'block';
                }
                
                if (podeEditar) {
                    document.getElementById('btnSalvarAlteracoes').style.display = 'block';
                    document.getElementById('btnExcluir').style.display = 'block';
                }
                
                modalAgendamento.show();
            }
        });
        
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
            fetch('/agendamento/novo', { method: 'POST', body: formData })
                .then(response => response.json())
                .then(data => {
                    const Toast = Swal.mixin({toast: true, position: 'top-end', showConfirmButton: false, timer: 3000, timerProgressBar: true});
                    if (data.success === false) {
                        Toast.fire({ icon: 'error', title: data.message });
                    } else if (data.success === true) {
                        Toast.fire({ icon: 'success', title: data.message });
                        calendar.refetchEvents();
                        
                        if (!document.getElementById('manterDados').checked) {
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
                    const Toast = Swal.mixin({toast: true, position: 'top-end', showConfirmButton: false, timer: 3000, timerProgressBar: true});
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
                            const Toast = Swal.mixin({toast: true, position: 'top-end', showConfirmButton: false, timer: 3000, timerProgressBar: true});
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
});