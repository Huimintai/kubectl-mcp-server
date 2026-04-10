FROM node:22-alpine

# Install azure-devops-mcp and supergateway globally
RUN npm install -g @azure-devops/mcp supergateway

# Non-root user (Kyverno compliance)
RUN addgroup -g 65532 nonroot && adduser -u 65532 -G nonroot -D nonroot
USER 65532

EXPOSE 8000

# supergateway wraps azure-devops-mcp stdio → streamable-http
# ADO_MCP_ORG and ADO_MCP_AUTH_TOKEN must be set via env
ENTRYPOINT ["sh", "-c", \
  "supergateway \
    --stdio \"npx -y @azure-devops/mcp ${ADO_MCP_ORG} --authentication envvar -d core,pipelines,repositories\" \
    --outputTransport streamableHttp \
    --port 8000 \
    --streamableHttpPath /mcp \
    --stateful"]
