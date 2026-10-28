
import { auth } from "@clerk/nextjs/server";

export async function POST(request: Request) {
  try {
    // 1. Validar que el usuario inició sesión en Clerk
    const { userId, getToken } = await auth();

    if (!userId) {
      return Response.json(
        {
          error:
            "Debes iniciar sesión para consultar el asistente RPA.",
        },
        { status: 401 }
      );
    }
    const isLocalDevelopment =
    process.env.NODE_ENV === "development";

    const isVercelPreview =
      process.env.VERCEL_ENV === "preview";

    if (!isLocalDevelopment && !isVercelPreview) {
      return Response.json(
        {
      error: "Integración no habilitada en producción.",
        },
        { status: 403 }
        );
    }


    // 3. Validar el contenido de la solicitud
    const body: unknown = await request.json();

    const question =
      typeof body === "object" &&
      body !== null &&
      "question" in body
        ? (body as { question?: unknown }).question
        : undefined;

    if (
      typeof question !== "string" ||
      !question.trim() ||
      question.length > 2000
    ) {
      return Response.json(
        {
          error:
            "La consulta debe tener entre 1 y 2000 caracteres.",
        },
        { status: 400 }
      );
    }

    // 4. Validar la URL del API Gateway
    const apiUrl = process.env.RAG_API_URL;

    if (!apiUrl) {
      return Response.json(
        {
          error: "No se configuró RAG_API_URL.",
        },
        { status: 503 }
      );
    }

    // 5. Obtener JWT de Clerk para AWS API Gateway
    const token = await getToken({
      template: "rpa-bsg-api",
    });

    if (!token) {
      return Response.json(
        {
          error:
            "No se pudo obtener el token de autenticación de Clerk.",
        },
        { status: 401 }
      );
    }

    // 6. Consultar el RAG mediante API Gateway HTTPS
    const response = await fetch(
      `${apiUrl.replace(/\/+$/, "")}/ask`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          question: question.trim(),
        }),
        cache: "no-store",
        signal: AbortSignal.timeout(60000),
      }
    );

    // 7. Gestionar errores del backend
    if (!response.ok) {
      console.error(
        "Error del API Gateway / RAG:",
        response.status
      );

      if (response.status === 401 || response.status === 403) {
        return Response.json(
          {
            error:
              "AWS rechazó el token de autenticación. Verifica la configuración JWT de Clerk.",
          },
          { status: 502 }
        );
      }

      return Response.json(
        {
          error:
            "El servicio RAG no pudo procesar la consulta.",
        },
        { status: 502 }
      );
    }

    // 8. Devolver respuesta y fuentes del RAG
    const data = await response.json();

    return Response.json(data, {
      headers: {
        "Cache-Control": "no-store",
      },
    });
  } catch (error) {
    if (error instanceof Error && error.name === "TimeoutError") {
      return Response.json(
        {
          error:
            "El servicio RAG excedió el tiempo máximo de respuesta.",
        },
        { status: 504 }
      );
    }

    console.error(
      "Error conectando con AWS:",
      error instanceof Error ? error.name : "UnknownError"
    );

    return Response.json(
      {
        error:
          "No fue posible conectar con el servicio RAG.",
      },
      { status: 502 }
    );
  }
}
