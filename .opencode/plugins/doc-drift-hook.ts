import type { Plugin } from "@opencode-ai/plugin"

let sessionCounter = 0
const CHECK_INTERVAL = 5
const PLUGIN_NAME = 'doc-drift-hook'

export const DocDriftHook: Plugin = async ({ client }) => {
  await client.app.log({
    body: { service: "doc-drift-hook", level: "info", message: "文档漂移检查钩子已加载" },
  })

  return {
    "tool.execute.before": async (input, output) => {
      if (input.tool === "bash" && typeof output.args?.command === "string") {
        const cmd = output.args.command.trim()
        if (/^git\s+(commit|add\s+.*\s*&&\s*git\s+commit)/i.test(cmd)) {
          await client.app.log({
            body: {
              service: "doc-drift-hook",
              level: "info",
              message: `[${PLUGIN_NAME}] 检测到 git commit 命令: ${cmd}`,
            },
          })
        }
      }
    },

    event: async ({ event }) => {
      await client.app.log({
        body: {
          service: "doc-drift-hook",
          level: "info",
          message: `[${PLUGIN_NAME}] event hook called: ${event.type}`,
        },
      })

      if (event.type === "session.idle") {
        sessionCounter++
        await client.app.log({
          body: {
            service: "doc-drift-hook",
            level: "info",
            message: `[${PLUGIN_NAME}] 会话计数: ${sessionCounter}/${CHECK_INTERVAL}`,
          },
        })

        if (sessionCounter >= CHECK_INTERVAL) {
          await client.app.log({
            body: {
              service: "doc-drift-hook",
              level: "warn",
              message: `[${PLUGIN_NAME}] 已累计 ${CHECK_INTERVAL} 次空闲会话，自动触发文档漂移检查`,
            },
          })

          const sessions = await client.session.list()
          const currentSession = sessions.data?.[sessions.data.length - 1]

          if (currentSession) {
            await client.session.promptAsync({
              path: { id: currentSession.id },
              body: {
                parts: [
                  {
                    type: "text",
                    text: "@doc-drift-checker 请检查文档漂移",
                  },
                ],
              },
            })
            await client.app.log({
              body: {
                service: "doc-drift-hook",
                level: "info",
                message: `[${PLUGIN_NAME}] 已向会话 ${currentSession.id} 发送文档漂移检查指令`,
              },
            })
          }

          sessionCounter = 0
        }
      }

      if (event.type === "session.created") {
        await client.app.log({
          body: {
            service: "doc-drift-hook",
            level: "info",
            message: `[${PLUGIN_NAME}] 新会话开始，当前计数: ${sessionCounter}/${CHECK_INTERVAL}`,
          },
        })
      }
    },
  }
}
