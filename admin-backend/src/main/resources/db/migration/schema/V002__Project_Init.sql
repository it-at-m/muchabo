CREATE TABLE model (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_name VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE chatbot (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL
);

CREATE TABLE chatbot_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chatbot_id UUID NOT NULL,
    model_id UUID NOT NULL,

    prompt TEXT NOT NULL,
    temperature DOUBLE PRECISION NOT NULL,
    version VARCHAR(20) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_chatbot_config_chatbot FOREIGN KEY (chatbot_id) REFERENCES chatbot(id),
    CONSTRAINT fk_chatbot_config_model FOREIGN KEY (model_id) REFERENCES model(id)
);
