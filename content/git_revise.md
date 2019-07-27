Title: Introducing git-revise
Date: 2019-07-27
Modified: 2019-07-27
Category: git
Tags: git, git-revise, rebase
Slug: git-revise
Authors: Nika Layzell
Status: draft

At Mozilla I often end up building my changes in a patch stack, and used `git
rebase -i`[^mozilla-hg] to make changes to commits in response to review
comments etc. Unfortunately, with a repository as large as
`mozilla-central`[^mc-files], `git rebase -i` has some downsides:

1. It's *slow*! Rebase operates directly on the worktree, so it performs a full
   checkout of each commit in the stack, and frequently refreshes worktree
   state. On large repositories (especially on NTFS) that can take a long time.

1. It *triggers rebuilds*! Because rebase touches the file tree, some build
   systems (like gecko's recursive-make backend) rebuild unnecessarially.

1. It's *stateful*! If the rebase fails, the repository is in a weird mid-rebase
   state, and in edge cases I've accidentally dropped commits due to other
   processes racing on the repository lock.
   
1. It's *clunky*! Common tasks (like splitting & rewording commits) require
   multiple steps and are unintuitive.

[^mozilla-hg]: I use `git` with `git cinnabar`, as I'm more comfortable with it,
    despite the official repos being mercurial.
[^mc-files]: 280268 files, according to `git ls-files | wc -l`.

Naturally, I did the **_only_ reasonable** thing: Build a brand-new tool.

| ![xkcd 927 - "Standards"]({attach}images/xkcd927.png) |
|------------------------------------------------------:|
| *source: [xkcd](https://xkcd.com/927/)*               |

# Introducing `git-revise`!

`git-revise` is a history editing tool designed for the patch-stack workflow.
It's fast, non-destructive, and aims to provide a familiar, powerful, and easy
to use re-imagining of the patch stack workflow.

## It's *fast*

I would never claim to be a *benchmarking expert* [^benchmark-expert], but
`git-revise` performs substantially better than rebase for small history editing
tasks [^system]. In a test applying a single-line change to a `mozilla-central`
commit 11 patches up the stack I saw a **30x** speed improvement.

```sh
$ time bash -c 'git commit --fixup=$TARGET; EDITOR=true git rebase -i --autosquash $TARGET~'
<snip>
real    0m16.931s
```

```sh
$ time git revise $TARGET
<snip>
real    0m0.541s
```

`git-revise` accomplishes this using an in-memory rebase algorithm operating
directly on git's trees, meaning it never has to touch your index or working
directory, avoiding expensive disk I/O!

The [performance](https://git-revise.readthedocs.io/en/latest/performance.html)
doc page has more details.

[^benchmark-expert]: I know my sample size of 1 sucks, though ^_^
[^system]: On my system, at least. I'm running Fedora 30 on an X1 Carbon (Gen 6)

## It's *handy*

`git-revise` isn't just a faster `git rebase -i`, it provides helpful commands,
flags, and tools which make common changes faster, and easier:

### Fixup Fast

```sh
$ git add .
$ git revise HEAD~~
```

Running `git revise $COMMIT` directly collects changes staged in the index, and
directly applies them to the specified commit. Conflicts are resolved
interactively, and a warning will be shown if the final state of the tree is
different from what you started with!

With an extra `-e`, you can update the commit message at the same time, and `-a`
will stage your changes, so you don't have to! [^revise-all]

[^revise-all]: The `-a` (or `--all`) flag will impact the index (due to files
    being staged), unlike other commands.

### Split Commits

```sh
$ git revise -c $COMMIT
Select changes to be included in part [1]:
diff --git b/file.txt a/file.txt
<snip>

Apply this hunk to index [y,n,q,a,d,e,?]?
```

Sometimes, a commit needs to be split in two, perhaps because a chance ended up
in the wrong commit. The `--cut` flag (and `cut` interactive command) provides a
fast way to split a commit in-place.

Running `git revise --cut $COMMIT` will start a `git add -p`-style hunk
selector, allowing you to pick changes for part 1, and the rest will end up in
part 2.

No more tinkering around with `edit` during a rebase to split off that comment
you accidentally added to the wrong commit!

### Interactive Mode

```sh
$ git revise -i
```

`git-revise` has a `git rebase -i`-style interactive mode, but with some
quality-of-life improvements, on top of being fast:

#### Implicit Base Commit

If a base commit isn't provided, `--interactive` will implicitly locate a safe
base commit to start from, walking up from `HEAD`, and stopping at published &
merge commits. Often `git revise -i` is all you need!

#### The `index` Todo

Staged changes in the index automatically appear in interactive mode, and can be
moved around and treated like any other commit in range. No need to turn it into
a commit with a dummy name before you pop open interactive mode & squash it into
another commit!

### Bulk Commit Rewording

```sh
$ git revise -ie
```

Ever wanted to update a bunch of commit messages at once? Perhaps they're all
missing the bug number? Well, `git revise -ie` has you covered. It'll open a
special Interactive Mode where each command is prefixed with a `++`, and the
full commit message is present after it.

Changes made to these commit messages will be applied before executing the
TODOs, meaning you can edit them in bulk. I use this _constantly_ to add bug
numbers, elaborate on commit details, and add reviewer information to commit
messages.

```
++ pick f5a02a16731a
Bug ??? - My commit summary, r=?

The full commit message body follows!

++ pick fef1aeddd6fb
Bug ??? - Another commit, r=?

Another commit's body!
```

### Autosquash Support

```sh
$ git rebase --autosquash
```

If you're used to `git rebase -i --autosquash`, revise works with you. Running
`git revise --autosquash` will automatically reorder and apply fixup commits
created with `git commit --fixup=$COMMIT` and similar tools, and thanks to the
implicit base commit, you don't even need to specify it.

You can even pass the `-i` flag if you want to edit the generated todo list
before running it.

## It's *non-destructive*

`git-revise` doesn't touch either your working directory, or your index. This
means that if it's killed while running, your repository won't be changed, and
you can't end up in a mid-rebase state while using it.

Problems like conflicts are resolved interactively, while the command is
running, without changing the actual files you've been working on. And, as no
files are touched, `git-revise` won't trigger any unnecessary rebuilds!

# Interested?

**_Awesome!_**

`git-revise` is a MIT-licensed pure-Python 3.6+ package, and can be installed
with `pip`:

```sh
$ python3 -m pip install --user git-revise
```

You can also check out the source on
[GitHub](https://github.com/mystor/git-revise), and read the
[manpage](https://git-revise.readthedocs.io/en/latest/man.html) online, or by
running `man git revise` in your terminal.

I'll leave you with some handy links to resources to learn more about
`git-revise`, how it works, and how you can contribute!

 * Repository: [https://github.com/mystor/git-revise](https://github.com/mystor/git-revise)
 * Bug Tracker: [https://github.com/mystor/git-revise/issues](https://github.com/mystor/git-revise/issues)
 * Manpage: [https://git-revise.readthedocs.io/en/latest/man.html](https://git-revise.readthedocs.io/en/latest/man.html)
 * Installing: [https://git-revise.readthedocs.io/en/latest/install.html](https://git-revise.readthedocs.io/en/latest/install.html)
 * Contributing: [https://git-revise.readthedocs.io/en/latest/contributing.html](https://git-revise.readthedocs.io/en/latest/contributing.html)
