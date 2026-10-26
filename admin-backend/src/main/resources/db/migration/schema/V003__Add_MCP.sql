CREATE TABLE mcp_server (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    url VARCHAR(255) NOT NULL
);

CREATE TABLE mcp_tool (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mcp_server_id UUID NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,

    CONSTRAINT fk_mcp_tool_server FOREIGN KEY (mcp_server_id) REFERENCES mcp_server(id) ON DELETE CASCADE
);

CREATE TABLE chatbot_tool (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chatbot_config_id UUID NOT NULL,
    mcp_tool_id UUID NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,

  CONSTRAINT fk_chatbot_tool_config FOREIGN KEY (chatbot_config_id) REFERENCES chatbot_config(id) ON DELETE CASCADE,
  CONSTRAINT fk_chatbot_tool_tool FOREIGN KEY (mcp_tool_id) REFERENCES mcp_tool(id) ON DELETE CASCADE,
  CONSTRAINT uq_chatbot_config_tool UNIQUE (chatbot_config_id, mcp_tool_id)
);
