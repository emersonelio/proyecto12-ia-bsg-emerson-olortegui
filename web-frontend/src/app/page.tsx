
import { auth } from "@clerk/nextjs/server";
import ChatClient from "./ChatClient";

export default async function Page() {
  const { isAuthenticated, redirectToSignIn } = await auth();

  if (!isAuthenticated) {
    return redirectToSignIn();
  }

  return <ChatClient />;
}
