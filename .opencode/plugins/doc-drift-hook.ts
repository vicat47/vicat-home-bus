import type { Plugin } from "@opencode-ai/plugin"

let sessionCounter = 0
const CHECK_INTERVAL = 5

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
              message: `检测到 git commit 命令: ${cmd}`,
            },
          })
        }
      }
    },

    "session.idle": async () => {
      sessionCounter++
      await client.app.log({
        body: {
          service: "doc-drift-hook",
          level: "info",
          message: `会话计数: ${sessionCounter}/${CHECK_INTERVAL}`,
        },
      })
    },

    "tui.prompt.append": async (input, output) => {
      if (sessionCounter >= CHECK_INTERVAL) {
        output.prompt +=
          "\n\n> 已累计 5 次会话，建议运行 @doc-drift-checker 检查文档漂移。"
        sessionCounter = 0
      }
    },
  }
}
