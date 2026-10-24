
"use client";

import { useState } from "react";
import { UserButton } from "@clerk/nextjs";

type SourceChunk = {
  document_id?: string | null;
  source_file?: string | null;
  chunk_id?: number | null;
  text: string;
};

type Message = {
  role: "user" | "assistant";
  content: string;
  sources?: SourceChunk[];
};

type ApiResponse = {
  question: string;
  answer: string;
  sources: SourceChunk[];
  error?: string;
};

const examples = [
  "¿Qué sucede si el robot no encuentra el archivo INPUT?",
  "Mi robot de Generación de Cronogramas PN falló. ¿Qué hago?",
  "Ejecuta ahora el robot de Generación de Cronogramas PN.",
];

const welcomeMessage: Message = {
  role: "assistant",
  content:
    "¡Hola! Soy tu asistente de documentación RPA. Puedo ayudarte a consultar procedimientos y excepciones documentadas en los PDD. ¿Qué necesitas saber?",
};

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([
    welcomeMessage,
  ]);

  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);

  async function sendMessage(value?: string) {
    const text = (value ?? question).trim();

    if (!text || loading) return;

    setMessages((previous) => [
      ...previous,
      {
        role: "user",
        content: text,
      },
    ]);

    setQuestion("");
    setLoading(true);

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          question: text,
        }),
      });

      const data = (await response.json()) as ApiResponse;

      if (!response.ok) {
        throw new Error(
          data.error || "No fue posible procesar la consulta."
        );
      }

      setMessages((previous) => [
        ...previous,
        {
          role: "assistant",
          content: data.answer,
          sources: data.sources ?? [],
        },
      ]);
    } catch (error) {
      const detail =
        error instanceof Error
          ? error.message
          : "Error desconocido.";

      setMessages((previous) => [
        ...previous,
        {
          role: "assistant",
          content: `No se pudo obtener una respuesta del RAG. ${detail}`,
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  function clearConversation() {
    if (loading) return;
    setMessages([welcomeMessage]);
    setQuestion("");
  }

  return (
    <div className="min-h-screen bg-slate-100 text-slate-900">
      <div className="mx-auto flex min-h-screen max-w-6xl flex-col bg-white shadow-xl">

        {/* Cabecera */}
        <header className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 px-6 py-5">
          <div>
            <p className="text-xs font-semibold uppercase tracking-widest text-blue-600">
              Plataforma de Inteligencia Artificial
            </p>

            <h1 className="mt-1 text-2xl font-bold">
              Asistente RPA
            </h1>

            <p className="text-sm text-slate-500">
              Consulta inteligente de documentación PDD
            </p>
          </div>

          <div className="flex items-center gap-3">
            <span className="rounded-full bg-green-100 px-3 py-2 text-xs font-medium text-green-800">
              Integración RAG · AWS
            </span>

            <button
              type="button"
              onClick={clearConversation}
              disabled={loading}
              className="rounded-lg border border-slate-200 px-3 py-2 text-xs hover:bg-slate-50 disabled:opacity-50"
            >
              Nueva conversación
            </button>
            <div className="flex items-center gap-2 border-l border-slate-200 pl-3">
               <UserButton showName />
            </div>
          </div>
        </header>

        {/* Documento */}
        <section className="border-b border-slate-200 bg-slate-50 px-6 py-4">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
            Documento configurado para la consulta
          </p>

          <p className="mt-1 font-semibold">
            Generación de Cronogramas PN
          </p>

          <p className="text-sm text-slate-500">
            PDD · Versión 1.0.2
          </p>
        </section>

        {/* Conversación */}
        <main className="flex-1 space-y-5 px-6 py-8">
          {messages.map((message, index) => (
            <div
              key={index}
              className={`flex ${
                message.role === "user"
                  ? "justify-end"
                  : "justify-start"
              }`}
            >
              <div
                className={`max-w-[90%] rounded-2xl p-4 shadow-sm ${
                  message.role === "user"
                    ? "bg-blue-700 text-white"
                    : "border border-slate-200 bg-slate-50"
                }`}
              >
                <p className="mb-2 text-xs font-semibold">
                  {message.role === "user"
                    ? "Tú"
                    : "Asistente RPA"}
                </p>

                <p className="whitespace-pre-wrap text-sm leading-7">
                  {message.content}
                </p>

                {message.sources &&
                  message.sources.length > 0 && (
                    <div className="mt-4 border-t border-slate-200 pt-3">
                      <p className="mb-2 text-xs font-semibold text-slate-500">
                        Fuentes recuperadas del PDD
                      </p>

                      <div className="space-y-2">
                        {message.sources.map((source, sourceIndex) => (
                          <details
                            key={sourceIndex}
                            className="rounded-lg border border-blue-100 bg-blue-50 p-3 text-xs text-blue-900"
                          >
                            <summary className="cursor-pointer font-semibold">
                              {source.source_file ??
                                "Documento sin nombre"}
                              {" · "}
                              Fragmento {source.chunk_id ?? "N/D"}
                            </summary>

                            <p className="mt-3 whitespace-pre-wrap leading-5">
                              {source.text}
                            </p>
                          </details>
                        ))}
                      </div>
                    </div>
                  )}
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex justify-start">
              <div className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-600">
                Consultando documentación RPA en AWS...
              </div>
            </div>
          )}
        </main>

        {/* Preguntas sugeridas */}
        <section className="px-6 pb-4">
          <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-slate-500">
            Consultas sugeridas
          </p>

          <div className="flex flex-wrap gap-2">
            {examples.map((example) => (
              <button
                key={example}
                type="button"
                disabled={loading}
                onClick={() => sendMessage(example)}
                className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-left text-xs text-slate-700 hover:border-blue-400 hover:bg-blue-50 disabled:opacity-50"
              >
                {example}
              </button>
            ))}
          </div>
        </section>

        {/* Entrada */}
        <form
          onSubmit={(event) => {
            event.preventDefault();
            void sendMessage();
          }}
          className="border-t border-slate-200 bg-white p-6"
        >
          <div className="flex items-end gap-3">
            <textarea
              value={question}
              onChange={(event) =>
                setQuestion(event.target.value)
              }
              placeholder="Escribe tu consulta sobre el PDD..."
              rows={2}
              maxLength={2000}
              disabled={loading}
              className="min-h-16 flex-1 resize-none rounded-xl border border-slate-300 px-4 py-3 text-sm outline-none focus:border-blue-600 disabled:bg-slate-100"
            />

            <button
              type="submit"
              disabled={!question.trim() || loading}
              className="rounded-xl bg-blue-700 px-5 py-4 text-sm font-semibold text-white hover:bg-blue-800 disabled:cursor-not-allowed disabled:opacity-40"
            >
              {loading ? "Consultando..." : "Enviar"}
            </button>
          </div>

          <p className="mt-3 text-center text-xs text-slate-400">
            Respuestas generadas desde el RAG de AWS.
            Verifica las fuentes antes de utilizar la información.
          </p>
        </form>
      </div>
    </div>
  );
}
