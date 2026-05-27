# API de Atividades da Mergington High School

Uma aplicação FastAPI super simples que permite aos alunos visualizar e se inscrever em atividades extracurriculares.

## Funcionalidades

- Visualizar todas as atividades extracurriculares disponíveis
- Inscrever-se em atividades
- Login de professores para ações administrativas
- Gerenciamento de anúncios (criar, editar, excluir)
- Exibição de anúncios ativos com datas de vigência

## Como começar

1. Instale as dependências:

   ```
   pip install fastapi uvicorn
   ```

2. Execute a aplicação:

   ```
   python app.py
   ```

3. Abra seu navegador e acesse:
   - Documentação da API: http://localhost:8000/docs
   - Documentação alternativa: http://localhost:8000/redoc

## Endpoints da API

| Método | Endpoint                                                          | Descrição                                                            |
| ------ | ----------------------------------------------------------------- | -------------------------------------------------------------------- |
| GET    | `/activities`                                                     | Obtém todas as atividades com detalhes e número atual de participantes |
| POST   | `/activities/{activity_name}/signup?email=student@mergington.edu` | Inscreve-se em uma atividade                                         |
| POST   | `/auth/login?username=...&password=...`                          | Realiza login de professor                                           |
| GET    | `/auth/check-session?username=...`                               | Valida sessão de professor                                           |
| GET    | `/announcements`                                                  | Lista anúncios ativos para o banner público                          |
| GET    | `/announcements/all?teacher_username=...`                        | Lista todos os anúncios para gestão (requer login)                  |
| POST   | `/announcements?teacher_username=...`                            | Cria anúncio (requer login)                                          |
| PUT    | `/announcements/{announcement_id}?teacher_username=...`          | Atualiza anúncio (requer login)                                      |
| DELETE | `/announcements/{announcement_id}?teacher_username=...`          | Exclui anúncio (requer login)                                        |

## Modelo de Dados

A aplicação usa um modelo de dados simples com identificadores significativos:

1. **Atividades** - Usa o nome da atividade como identificador:
   - Descrição
   - Horário
   - Número máximo de participantes permitidos
   - Lista de e-mails dos alunos inscritos

2. **Alunos** - Usa o e-mail como identificador:
   - Nome
   - Série

Todos os dados são armazenados no MongoDB configurado em `backend/database.py`.
