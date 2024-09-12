
# YouTube Transcript API com Proxy Rotativo

Este projeto implementa uma API FastAPI para obter transcrições de vídeos do YouTube usando um sistema de proxy rotativo. Ele utiliza a biblioteca `youtube_transcript_api` para obter as transcrições e um gerenciador de proxies gratuitos para contornar possíveis limitações de taxa.

## Características

- Obtenção de transcrições de vídeos do YouTube
- Sistema de proxy rotativo para evitar bloqueios e limitações de taxa
- Atualização periódica automática da lista de proxies
- Tratamento de erros robusto
- Logging detalhado para facilitar a depuração

## Requisitos

- Python 3.7+
- FastAPI
- Pydantic
- youtube_transcript_api
- FreeProxyManager (implementação personalizada)

## Instalação

1. Clone o repositório:
   ```
   git clone https://github.com/seu-usuario/youtube-transcript-api-proxy.git
   cd youtube-transcript-api-proxy
   ```

2. Instale as dependências:
   ```
   pip install -r requirements.txt
   ```

## Uso

1. Inicie o servidor FastAPI:
   ```
   uvicorn main:app --reload
   ```

2. A API estará disponível em `http://localhost:8000`

3. Para obter a transcrição de um vídeo, faça uma requisição POST para `/transcript` com o seguinte corpo JSON:
   ```json
   {
     "video_id": "ID_DO_VIDEO_DO_YOUTUBE"
   }
   ```

   Exemplo usando curl:
   ```
   curl -X POST "http://localhost:8000/transcript" -H "Content-Type: application/json" -d '{"video_id":"29XE10UEooc"}'
   ```

## Endpoints

- `GET /`: Retorna uma mensagem de boas-vindas
- `POST /transcript`: Recebe o ID de um vídeo do YouTube e retorna sua transcrição

## Estrutura do Projeto

- `main.py`: Arquivo principal contendo a lógica da API
- `FreeProxyManager.py`: Implementação do gerenciador de proxies (não incluído neste repositório)

## Configuração

O projeto usa variáveis de ambiente para configuração. Certifique-se de definir as seguintes variáveis, se necessário:

- `PROXY_UPDATE_INTERVAL`: Intervalo em segundos para atualização da lista de proxies (padrão: 3600)

## Tratamento de Erros

A API trata os seguintes erros específicos:

- Legendas desativadas para o vídeo
- Nenhuma transcrição encontrada
- Vídeo indisponível
- Erros inesperados

Em cada caso, uma resposta HTTP apropriada é retornada com uma mensagem de erro descritiva.

## Logs

O projeto utiliza o módulo `logging` do Python para registrar informações importantes. Os logs incluem:

- Inicialização e encerramento da aplicação
- Atualizações da lista de proxies
- Detalhes sobre as solicitações de transcrição
- Erros e exceções

## Aviso Legal e Considerações Éticas

**IMPORTANTE: Este projeto destina-se apenas para uso pessoal e fins educacionais.**

Ao usar este projeto, esteja ciente das seguintes considerações:

1. **Uso Responsável**: Esta ferramenta deve ser usada apenas para hobby e fins educacionais. Não é destinada para uso comercial ou em larga escala.

2. **Termos de Serviço do YouTube**: O uso deste projeto pode não estar totalmente alinhado com os Termos de Serviço do YouTube. O YouTube desencoraja o uso de métodos automatizados para acessar seu serviço sem permissão explícita.

3. **Limitações de Uso**: Recomenda-se fortemente limitar a frequência e o volume de solicitações para evitar sobrecarregar os servidores do YouTube ou violar suas políticas de uso.

4. **Direitos Autorais**: Respeite os direitos autorais dos criadores de conteúdo. As transcrições obtidas não devem ser redistribuídas ou usadas de maneira que viole os direitos dos proprietários do conteúdo.

5. **Não há Garantias**: Este projeto é fornecido "como está", sem garantias de qualquer tipo. Os usuários são responsáveis por seu próprio uso e por quaisquer consequências que possam surgir.

6. **Mudanças nas Políticas**: As políticas do YouTube podem mudar. É responsabilidade do usuário manter-se atualizado sobre os termos de serviço e políticas do YouTube.

7. **Uso Ético**: Considere o impacto ético de suas ações. Use esta ferramenta de maneira responsável e considere como seu uso pode afetar os criadores de conteúdo e a plataforma YouTube.

Ao usar este projeto, você reconhece que entendeu estas considerações e concorda em usar a ferramenta de maneira responsável e ética.

## Contribuindo

Contribuições são bem-vindas! Por favor, sinta-se à vontade para submeter pull requests ou abrir issues para discutir possíveis melhorias ou relatar bugs.

