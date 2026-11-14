import NextAuth from "next-auth";

const issuer = process.env.AUTH_OIDC_ISSUER;
const clientId = process.env.AUTH_OIDC_CLIENT_ID;
const clientSecret = process.env.AUTH_OIDC_CLIENT_SECRET;
const audience = process.env.AUTH_OIDC_AUDIENCE;
const authSecret = process.env.AUTH_SECRET || "smartdoctor-local-development-secret-change-before-deploy";

if (process.env.APP_ENV === "production") {
  if (!process.env.AUTH_SECRET || process.env.AUTH_SECRET.length < 32 || /local-only|replace-with|change-before-deploy/i.test(process.env.AUTH_SECRET)) {
    throw new Error("Production requires a unique AUTH_SECRET with at least 32 characters.");
  }
  if (!issuer || !clientId || !clientSecret) {
    throw new Error("Production requires AUTH_OIDC_ISSUER, AUTH_OIDC_CLIENT_ID and AUTH_OIDC_CLIENT_SECRET.");
  }
}

const providers = issuer && clientId && clientSecret ? [{
  id: "smartdoctor-oidc",
  name: process.env.AUTH_OIDC_PROVIDER_NAME || "Organization account",
  type: "oidc" as const,
  issuer,
  clientId,
  clientSecret,
  idToken: true,
  checks: ["pkce", "state", "nonce"] as ("pkce" | "state" | "nonce")[],
  authorization: { params: {
    scope: process.env.AUTH_OIDC_SCOPE || "openid profile email",
    ...(audience ? { audience } : {}),
  }},
  profile(profile: Record<string, unknown>) {
    return {
      id: String(profile.sub || ""),
      name: typeof profile.name === "string" ? profile.name : null,
      email: typeof profile.email === "string" ? profile.email : null,
      image: typeof profile.picture === "string" ? profile.picture : null,
    };
  },
}] : [];

export const { handlers, auth, signIn, signOut } = NextAuth({
  providers,
  secret: authSecret,
  trustHost: process.env.AUTH_TRUST_HOST === "true",
  session: { strategy: "jwt", maxAge: 8 * 60 * 60 },
  pages: { signIn: "/login" },
  callbacks: {
    async signIn({ account }) {
      return Boolean(account?.access_token);
    },
    async jwt({ token, account }) {
      if (account?.access_token) {
        token.accessToken = account.access_token;
        token.accessTokenExpires = account.expires_at
          ? account.expires_at * 1000
          : Date.now() + 60 * 60 * 1000;
        token.authError = undefined;
      }
      if (token.accessTokenExpires && Date.now() >= token.accessTokenExpires) {
        token.authError = "AccessTokenExpired";
      }
      return token;
    },
    async session({ session, token }) {
      if (session.user) session.user.id = token.sub || "";
      if (token.authError) session.error = token.authError;
      return session;
    },
  },
});