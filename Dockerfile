# ===== GozoLite Runtime — Ubuntu 22.04 (sin Nim, con TypeScript/ts-node) =====
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive \
    TZ=Etc/UTC \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    PATH=/root/.cargo/bin:/usr/local/go/bin:$PATH

# ---------- Base & utilidades ----------
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl wget gnupg lsb-release software-properties-common \
    build-essential pkg-config make zip unzip git xz-utils tar \
    bash dash tzdata file \
    # shells / scripting y CLI de apoyo
    gawk sed grep coreutils bc \
    # DB/CLI
    sqlite3 \
    # Lenguajes base (APT)
    python3 python3-pip python3-venv \
    openjdk-17-jdk maven gradle \
    golang \
    ruby-full \
    php-cli php-xml php-mbstring \
    perl \
    r-base \
    lua5.4 \
    ocaml \
    gfortran \
    # Haskell
    ghc haskell-stack cabal-install \
    # Ada / Pascal / COBOL
    gnat fpc gnucobol \
    # Tcl
    tcl \
    # Scala toolchain (sin sbt)
    scala \
    # Miscelánea
    apt-transport-https dirmngr gpg-agent \
 && rm -rf /var/lib/apt/lists/*

# ---------- Node.js 20.x (NodeSource) ----------
RUN mkdir -p /etc/apt/keyrings \
 && curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key \
 | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg \
 && echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_20.x nodistro main" \
    > /etc/apt/sources.list.d/nodesource.list \
 && apt-get update && apt-get install -y --no-install-recommends nodejs \
 && node -v && npm -v \
 && rm -rf /var/lib/apt/lists/*

# ---------- TypeScript runtime (global) ----------
RUN npm install -g --omit=dev typescript ts-node \
 && ts-node -v && tsc -v

# Fix global para ts-node (evita TS5109)
ENV TS_NODE_TRANSPILE_ONLY=1 \
    TS_NODE_COMPILER_OPTIONS='{"module":"CommonJS","moduleResolution":"Node"}'

# ---------- Rust (rustup minimal) ----------
RUN curl https://sh.rustup.rs -sSf | sh -s -- -y --profile minimal \
 && rustc -V && cargo -V

# ---------- Kotlin (sobre JDK 17) vía SDKMAN ----------
SHELL ["/bin/bash", "-lc"]
RUN curl -s "https://get.sdkman.io" | bash \
 && source "/root/.sdkman/bin/sdkman-init.sh" \
 && sdk install kotlin \
 && echo 'source "/root/.sdkman/bin/sdkman-init.sh"' >> /root/.bashrc

# ---------- Dart ----------
RUN curl -fsSL https://dl-ssl.google.com/linux/linux_signing_key.pub \
 | gpg --dearmor -o /usr/share/keyrings/dart.gpg \
 && echo "deb [signed-by=/usr/share/keyrings/dart.gpg] https://storage.googleapis.com/download.dartlang.org/linux/debian stable main" \
    > /etc/apt/sources.list.d/dart_stable.list \
 && apt-get update && apt-get install -y --no-install-recommends dart \
 && rm -rf /var/lib/apt/lists/*

# ---------- Zig (binario oficial; caché separable en runtime) ----------
ARG ZIG_VERSION=0.11.0
RUN mkdir -p /opt/zig \
 && curl -fsSL https://ziglang.org/download/${ZIG_VERSION}/zig-linux-x86_64-${ZIG_VERSION}.tar.xz \
 | tar -xJ -C /opt/zig --strip-components=1 \
 && ln -s /opt/zig/zig /usr/local/bin/zig \
 && zig version

# ---------- Warm-ups (evitan primer “frío”) ----------
WORKDIR /opt/warmups
RUN set -eux; \
  printf 'public class Main{public static void main(String[]a){System.out.println("hello java");}}' > Main.java; \
  javac Main.java; java Main; \
  printf 'object Main extends App { println("hello scala") }' > Main.scala; \
  scalac Main.scala; scala -nc Main; \
  printf 'main = putStrLn "hello haskell"\n' > Main.hs; \
  runghc Main.hs; \
  printf 'console.log("hello node")\n' > main.js; \
  node main.js; \
  printf 'console.log("hello typescript")\n' > main.ts; \
  ts-node main.ts; \
  printf 'pub fn main() void { @import("std").debug.print("hello zig\\n", .{}); }' > main.zig; \
  ZIG_GLOBAL_CACHE_DIR=/opt/zig-cache ZIG_LOCAL_CACHE_DIR=/opt/zig-cache zig build-exe main.zig && ./main; \
  printf 'program H; print *, "hello fortran"; end program H\n' > h.f90; \
  gfortran -O2 -o h.out h.f90 && ./h.out; \
  printf "program Hello; begin writeln('hello pascal'); end.\n" > hello.pas; \
  fpc -O2 -ohp.out hello.pas && ./hp.out; \
  printf '       IDENTIFICATION DIVISION.\n       PROGRAM-ID. HELLO.\n       PROCEDURE DIVISION.\n           DISPLAY "hello cobol".\n           STOP RUN.\n' > hello.cob; \
  cobc -x -O2 -o hc.out hello.cob && ./hc.out; \
  printf 'fun main(){ println("hello kotlin") }\n' > kt.kt; \
  kotlinc kt.kt -include-runtime -d kt.jar && java -jar kt.jar; \
  printf 'void main(){ print("hello dart"); }\n' > main.dart; \
  dart run main.dart; \
  rm -rf /opt/zig-cache || true

# ---------- Usuario no-root (sin sudoers) ----------
RUN useradd -m -s /bin/bash runner
USER runner
WORKDIR /home/runner

# ---------- Entorno por defecto para GozoLite ----------
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# La orden real la define docker-compose (uvicorn o smoke)
CMD ["bash","-lc","python3 --version && node -v && ts-node -v && javac -version && echo 'Runtime OK'"]