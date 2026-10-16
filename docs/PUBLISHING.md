# 将分发包发布到 GitHub

## 当前交付与目标

**准备好文件不代表已推送远程仓库。**发布后以远程分支和文件哈希回读为准。下面区分“创建新仓库”与“上传到已经存在的空仓库”；辅助脚本只负责前者，不能因为已有目标而另建仓库或强推。

本包默认发布目标为 `fuhaooo/jjf-external-deck-skill`。README 已按该名称编写安装命令。选择其他名称时，必须先同步更新 README 并重新审阅文件清单；辅助脚本会检查安装命令是否包含目标仓库名。

## 创建新的远程仓库（WSL / Linux / macOS / Windows）

先将完整发布包解压，进入包含 README.md、scripts/、skills/ 的仓库根目录。需要 Git、Python 3.10+ 和 GitHub CLI；请按 [GitHub CLI 官方安装说明](https://cli.github.com/) 安装。

只在自己的终端登录，不在聊天、README 或仓库中粘贴 Token：

```bash
gh auth login --hostname github.com --git-protocol https --web
gh auth status --hostname github.com
# 如 git 尚未使用 gh 登录，按需执行官方的凭据助手配置：
gh auth setup-git
```

检查将发生的动作（不会访问 GitHub 或创建仓库）：

```bash
python3 scripts/publish_github.py --owner fuhaooo --public
```

确认需要公开，让所有有网络访问的人可查看和安装后执行：

```bash
python3 scripts/publish_github.py --owner fuhaooo --public --execute
```

希望仅授权协作者可访问则将 `--public` 改为 `--private`。原生 Windows 将 `python3` 换成 `python`。

发布脚本使用已登录的 GitHub CLI；它不会索取、输出或复制 Token。它会检查：

1. 文件哈希与正式 Logo、Skill 目录、发布边界。
2. 当前登录账号与 `--owner` 一致；此脚本只处理个人账号，不猜测组织权限。
3. 远程名称不存在、本地目录没有已有提交或远程关联。
4. 初始化 main，暂存明确清单中的文件，以当前 GitHub 账号的 noreply 邮箱提交。
5. 使用 `gh repo create --source --remote --push` 创建并推送。
6. 再次读取远程：仓库身份、可见性、默认分支、本地/远程 commit、README blob 均一致才输出 `VERIFIED`。

成功证据另写入本地 `.publication.json`，该文件被 Git 忽略。脚本不自动发布 Release、不设置开源许可证、不改写已有仓库、不 force-push、不删除失败后的进度。

## 中途失败时

### 用户已创建目标空仓库

已存在且经确认没有任何远程分支的目标，不需要再次运行`gh repo create`。先检查仓库身份、可见性、写入权限和`git ls-remote <目标URL>`的成功退出码及空结果。网络失败不等于空仓库。Git可能已有可用的系统凭据助手，即使`gh auth status`未登录也不能据此断言Git无法推送；不要读取或输出助手保存的Token。

本地目录还不是Git仓库时，在确认范围内初始化main；已有Git目录则先查看状态和remote，不覆盖。以本仓库为例：

```bash
python scripts/check_release.py
git init -b main
git remote add origin https://github.com/fuhaooo/jjf-external-deck-skill.git
```

暂存`REPOSITORY.sha256`中的明确文件清单和该清单本身，核对暂存差异后正常commit、`git push -u origin main`，不使用force。提交使用维护者确认的身份/noreply邮箱。若远端已有分支或文件，先fetch比较并保留其历史，不能套空仓库初始化流程。

推送后重新读取远端默认分支、commit、README及SVG文件blob，确认与本地一致才报告成功。已有目标的可见性保持原状，不能从“上传”推断更改可见性的授权。

### 创建或推送只完成一部分

不要直接重复创建，也不要删除已经创建的仓库。先在自己的终端查看：

```bash
git status
git remote -v
gh repo view fuhaooo/jjf-external-deck-skill
```

已经创建远程且 origin 正确、仅 push 失败时，排除网络／凭据问题后执行：

```bash
gh auth setup-git
git push -u origin main
```

如果目录尚未建立 origin，先检查远程仓库确实属于自己且为空，再自行关联；不要盲目覆盖已有 remote。已有本地提交或已存在目标仓库时，辅助脚本会拒绝重新初始化，由维护者核对后正常提交／推送。

只有远程默认分支与内容都正确，才发布安装地址。校验示例：

```bash
gh repo view fuhaooo/jjf-external-deck-skill --json url,isPrivate,defaultBranchRef
git rev-parse HEAD
git ls-remote origin refs/heads/main
gh api repos/fuhaooo/jjf-external-deck-skill/contents/README.md?ref=main --jq .sha
git hash-object README.md
```

前两项 SHA 应对应；README 的远程 blob SHA 应与本地 `git hash-object` 相同。发布后再从干净目录验证发现与安装：

```bash
npx skills@latest add fuhaooo/jjf-external-deck-skill --list
```

## 维护规范

只提交 Skill 和公开文档。Deck 项目、客户素材和私有附件放在其他目录，不能以“打包全部文件”方式混入。

修改后运行两组测试，并审阅变更。`REPOSITORY.sha256` 是防误改检查，不是签名或完整安全保证。更新文件校验值前逐项确认内容可发布；不要为消除报错而自动接纳未知文件。

原有 Skill 的校验清单是 `skills/jjf-external-deck/MANIFEST.sha256`，其路径相对该 Skill 根目录。仓库清单路径则相对仓库根目录。发布材料不包含字体，也不声明已经完成真实图片转换或 Canva 联调。

参考：[gh repo create](https://cli.github.com/manual/gh_repo_create)、[gh auth login](https://cli.github.com/manual/gh_auth_login)、[gh auth setup-git](https://cli.github.com/manual/gh_auth_setup-git)。
