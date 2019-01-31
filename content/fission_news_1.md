Title: Fission Engineering Newsletter #1
Date: 2018-01-31 3:00pm
Modified: 2018-01-31 3:00pm
Category: Programming
Tags: mozilla, firefox, gecko, fission
Slug: fission-news-1
Authors: Nika Layzell
Status: draft

A little more a year ago, a serious security flaw affecting almost all modern
processors was [publicly disclosed]. Three known variants of the issue
were announced with the names dubbed as [Spectre] (variants 1 and 2) and
[Meltdown] (variant 3). Spectre abuses a CPU optimization technique known
as speculative execution to exfiltrate secret data stored in memory of other
running programs via side channels. This might include cryptographic keys,
passwords stored in a password manager or browser, cookies, etc. This timing
attack posed a serious threat to the browsers because webpages often serve
JavaScript from multiple domains that run in the same process. This
vulnerability would enable malicious third-party code to steal sensitive user
data belonging to a site hosting that code, a serious flaw that would violate
a web security cornerstone known as [Same-origin policy].

Thanks to the heroic efforts of the Firefox JS and Security teams, we were
able to mitigate these vulnerabilities right away. However, these mitigations
may not save us in the future if another security vulnerability is released
exploiting the same underlying problem of sharing processes (and hence,
memory) between different domains, some of which may be malicious. Chrome
spent multiple years working to isolate sites in their own processes.

We aim to build a browser which isn't just secure against known security
vulnerabilities, but also has layers of built-in defense against potential
future vulnerabilities. To accomplish this, we need to revamp the
architecture of Firefox and support full Site Isolation. We call this next
step in the evolution of Firefox’s process model "**Project Fission**". While
Electrolysis split our browser into Content and Chrome, with Fission, we will
"split the atom", splitting cross-site iframes into different processes than
their parent frame.

Over the last year, we have been working to lay the groundwork for Fission,
designing new infrastructure. In the coming weeks and months, we’ll need help
from all Firefox teams to adapt our code to a post-Fission browser
architecture.


### Planning and Coordination

Fission is a massive project, spanning across many different teams, so keeping
track of what everyone is doing is a pretty big task. While we have a weekly
project meeting, which someone on your team may already be attending, we have
started also using a Bugzilla project tracking flag to keep track of the work
we have in progress.

Now that we've moved past much of the initial infrastructure ground work, we
are going to keep track of work with our milestone targets. Each milestone
will contain a collection of new features and improved functionality which
brings us incrementally closer to our goal.

Our first milestone, "Milestone 1" (clever, I know), is currently targeted
for the end of February. In Milestone 1, we plan to have the groundwork for
out-of-process iframes, which encompasses some major work, including, but not
limited to, the following contributions:

* **:rhunt** is implementing basic out-of-process iframe rendering behind a
  pref. ([Bug 1500257])
* **:jdai** is implementing native JS Window Actor APIs to migrate FrameScripts.
  ([Bug 1467212])
* **:farre** is adding support for BrowsingContext fields to be
  synchronized between multiple content processes. ([Bug 1523645])
* **:peterv** has implemented new cross-process WindowProxy objects to
  correctly emulate the `Window` object APIs exposed to cross-origin documents.
  ([Bug 1353867])
* **:mattn** is converting the FormAutoFillListeners code to the actors infrastructure. ([Bug 1474143])
* **:felipe** simulated the Fission API for communicating between parent and child processes. ([Bug 1493984])
* **:heycam** is working on sharing UA stylesheets between processes. ([Bug 1474793])
* **:kmag**, **:erahm** and many others have reduced per-process memory overhead!
* **:jld** is working on async process launches
* **:dragana**, **:kershaw** and others are moving networking logic into a socket process. ([Bug 1322426])
* ...and so much more!

If you want an up-to-date view of Milestone 1, you can see the [current Milestone 1 status]
on Bugzilla.

If have a bug which may be relevant to fission, *please* let us know by setting
the "Fission Milestone" project flag to '?'. We'll swing by and triage it into
the correct milestone.

![Setting Fission Milestone Project Flag]({attach}images/fission_milestone_select.png)


If you have any questions, feel free to reach out to one of us, and we'll get
you answers, or guide you to someone who can:

* Ron Manning `<rmanning@mozilla.com>` (Fission EPM)
* Nika Layzell `<nika@mozilla.com>` (Fission Tech Lead)
* Neha Kochar `<nkochar@mozilla.com>` (DOM Fission Engineering Manager)


### What's Changing?

In order to make each component of Firefox successfully adapt to a post-Fission
world, many of them are going to need changes of varying scale. Covering all of
the changes which we're going to need would be impossible within a single
newsletter. Instead, I will focus on the changes to actors, messageManagers,
and document hierarchies.

Today, Firefox has process separation between the UI - run in the *parent
process*, and web content - run in *content processes*. Communication between
these two trees of "Browsing Contexts" is done using the `TabParent` and
`TabChild` actors in C++ code, and Message Managers in JS code. These systems
communicate directly between the "embedder", which in this case is the
`<browser>` element, and the root of the embedded tree, which in this case
would be the toplevel DocShell in the tab.

However, in a post-Fission world, this layer for communication is no longer
sufficient. It will be possible for multiple processes to render distinct
subframes, meaning that each tab has multiple connected processes.

Components will need to adapt their IPC code to work in this new world, both by
updating their use of existing APIs, and by adapting to use new Actors and APIs
which are being added as part of the Fission project.


#### Per-Window Global Actors

For many components, the full tree of Browsing Contexts is not important,
rather communication is needed between the parent process and any specific
document. For these cases, a new actor has been added which is exposed both in
C++ code and JS code called [PWindowGlobal].

Unlike other actors in gecko, such as `Tab{Parent,Child}`, this actor exists
for all window globals, including those loaded within the parent process. This
is handled using a new `PInProcess` manager actor, which supports sending main
thread to main thread IPDL messages.

JS code running within a FrameScript may not be able to inspect every frame at
once, and won't be able to handle events from out of process iframes. Instead,
it will need to use our new [JS Window Actor] APIs, which we are targeting to
land in Milestone 1. These actors are "managed" by the `WindowGlobal` actors,
and are implemented as JS classes instantiated when requested for any
particular window. They support sending async messages, and will be present for
both in-process and out-of-process windows.

C++ logic which walks the frame tree from the `TabChild` may stop working.
Instead, C++ code may choose to use the PWindowGlobal actor to send messages in
a manner similar to JS code.

#### `BrowsingContext` objects

C++ code may also maintain shared state on the `BrowsingContext` object. We are
targeting landing the field syncing infrastructure in Milestone 1, and it will
provide a place to store data which should be readable by all processes with a
view of the structure.

The parent process holds a special subclass of the `BrowsingContext` object:
`CanonicalBrowsingContext`. This object has extra fields which can be used in
the parent to keep track of the current status of all frames in one place.

#### `TabParent`, `TabChild` and IFrames

The `Tab{Parent,Child}` actors will continue to exist, and will always bridge
from the parent process to a content process. However, in addition to these
actors being present for toplevel documents, they will also be present for
out-of-process subtrees.

As an example, consider the following tree of nested browsing contexts:

```
         +-- 1 --+
         | a.com |
         +-------+
          /     \
    +-- 2 --+ +-- 4 --+
    | a.com | | b.com |
    +-------+ +-------+
        |         |
    +-- 3 --+ +-- 5 --+
    | b.com | | b.com |
    +-------+ +-------+
```

Under e10s, we have a single `Tab{Parent,Child}` pair for the entire tab, which
would connect to `1`, and FrameScripts would run with `content` being the `1`'s
global.

After Fission, there will still be a `Tab{Parent,Child}` actor for the root of
the tree, at `1`. However, there will also be two additional `Tab{Parent,Child}`
actors: one at `3` and one at `4`. Each of these nested `TabParent` objects are
held alive in the parent process by a `RemoteFrameParent` actor whose
corresponding `RemoteFrameChild` is held by the embedder's iframe.

The following is a diagram of the documents and actors which build up the actor
tree, excluding the `WindowGlobal` actors. `RF{P,C}` stands for
`RemoteFrame{Parent,Child}`, and `T{P,C}` stands for `Tab{Parent,Child}`.
The `RemoteFrame` actors are managed by their embedding `Tab` actors, and use
the same underlying transport.

```
- within a.com's process -

         +-------+
         | TC: 1 |
         +-------+
             |
         +-- 1 --+
         | a.com |
         +-------+
          /     \
    +-- 2 --+ +-------+
    | a.com | | RFC:2 |
    +-------+ +-------+
        |
    +-------+
    | RFC:1 |
    +-------+

- within b.com's process -

    +-------+    +-------+
    | TC: 2 |    | TC: 3 |
    +-------+    +-------+
        |            |
    +-- 3 --+    +-- 4 --+
    | b.com |    | b.com |
    +-------+    +-------+
                     |
                 +-- 5 --+
                 | b.com |
                 +-------+

- within the parent process -

         +-------+
         | TP: 1 |
         +-------+
          /     \    (manages)
    +-------+ +-------+
    | RFP:1 | | RFP:2 |
    +-------+ +-------+
        |         |
    +-------+ +-------+
    | TP: 2 | | TP: 3 |
    +-------+ +-------+
```


### This Newsletter

I hope to begin keeping everyone updated on the latest developments with
Fission over the coming months, but am not quite ready to commit to a weekly or
bi-weekly newsletter schedule.

If you're interested in helping out with the newsletter, please reach out and
let me (Nika) know!.


### TL;DR

Fission is happening and our first "Milestone" is targeted at the end of
February. Please file bugs related to fission and mark them as "Fission
Milestone: ?" so we can triage them into the correct milestone.


---

*Thanks for reading, and best of luck splitting the atom!*

[The Project Fission Team]


[publicly disclosed]: https://googleprojectzero.blogspot.com/2018/01/reading-privileged-memory-with-side.html
[Spectre]: https://spectreattack.com/spectre.pdf
[Meltdown]: https://meltdownattack.com/meltdown.pdf
[Same-origin policy]: https://en.m.wikipedia.org/wiki/Same-origin_policy
[Bug 1500257]: https://bugzilla.mozilla.org/show_bug.cgi?id=1500257
[Bug 1467212]: https://bugzilla.mozilla.org/show_bug.cgi?id=1467212
[Bug 1523645]: https://bugzilla.mozilla.org/show_bug.cgi?id=1523645
[Bug 1353867]: https://bugzilla.mozilla.org/show_bug.cgi?id=1353867
[Bug 1474143]: https://bugzilla.mozilla.org/show_bug.cgi?id=1474143
[Bug 1513045]: https://bugzilla.mozilla.org/show_bug.cgi?id=1513045
[Bug 1493984]: https://bugzilla.mozilla.org/show_bug.cgi?id=1493984
[Bug 1474793]: https://bugzilla.mozilla.org/show_bug.cgi?id=1474793
[Bug 1322426]: https://bugzilla.mozilla.org/show_bug.cgi?id=1322426
[current Milestone 1 status]: https://bugzilla.mozilla.org/buglist.cgi?classification=Client%20Software&classification=Developer%20Infrastructure&classification=Components&classification=Server%20Software&classification=Other&f1=cf_fission_milestone&list_id=14538804&o1=equals&query_format=advanced&v1=M1&query_based_on=&columnlist=product%2Ccomponent%2Cassigned_to%2Cshort_desc%2Cbug_status%2Cresolution%2Cstatus_whiteboard
[The Project Fission Team]: https://wiki.mozilla.org/Project_Fission#Team
