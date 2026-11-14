"""Concise, complete lesson bank for every curriculum topic."""

from app.curriculum import TOPICS


NOTES = {
    "python-colab-markdown": ("Names reference objects; notebooks pair executable code with explanations.", r"`b = a` aliases a mutable object. Write inline math as $w^\top x+b$ and display math as $$L=\frac1n\sum_i(\hat y_i-y_i)^2.$$"),
    "numpy-foundations": ("An array is data plus shape and dtype; vectorization applies one operation to whole axes.", r"For $A\in\mathbb R^{m\times k}$ and $B\in\mathbb R^{k\times n}$, $(AB)_{ij}=\sum_r A_{ir}B_{rj}$. Broadcasting aligns dimensions from the right."),
    "linear-algebra-i": ("A matrix represents a linear map; columns show where basis vectors go.", r"$T(ax+by)=aT(x)+bT(y)$. Rank is the dimension of the image and rank-nullity says $\operatorname{rank}A+\operatorname{nullity}A=n$."),
    "linear-algebra-ii": ("Eigenvectors are invariant directions; SVD describes every matrix as rotate-scale-rotate.", r"$Av=\lambda v$ and $A=U\Sigma V^\top$. For centered $X$, PCA keeps top eigenvectors of $X^\top X/n$."),
    "probability-statistics": ("Probability quantifies uncertainty; expectation is a weighted average over outcomes.", r"$P(A\mid B)=P(A\cap B)/P(B)$, Bayes gives $P(H\mid E)\propto P(E\mid H)P(H)$, and $\operatorname{Var}X=E[X^2]-E[X]^2$."),
    "calculus-optimization": ("The gradient gives local steepest ascent, so optimization steps in its negative direction.", r"$\theta_{t+1}=\theta_t-\eta\nabla L(\theta_t)$. Convexity means $f(tx+(1-t)y)\le tf(x)+(1-t)f(y)$."),
    "data-science-tools": ("A sound workflow separates data inspection, preprocessing, training, and untouched evaluation.", r"Standardization uses $z=(x-\mu_{\rm train})/\sigma_{\rm train}$. Fit every transform on training data only to prevent leakage."),
    "supervised-learning-i": ("Supervised models learn a map from features to labeled targets.", r"OLS minimizes $\|Xw-y\|_2^2$; one solution is $w=X^+y$. Logistic regression uses $p(y=1\mid x)=\sigma(w^\top x+b)$."),
    "supervised-learning-ii": ("Different inductive biases trade smoothness, locality, margin, and interpretability.", r"SVMs maximize geometric margin; kernels use $K_{ij}=k(x_i,x_j)$. Precision is $TP/(TP+FP)$ and recall is $TP/(TP+FN)$."),
    "unsupervised-learning": ("Unsupervised learning searches for structure without target labels.", r"K-means minimizes $\sum_i\|x_i-\mu_{c_i}\|^2$. PCA gives the best rank-$k$ linear reconstruction under squared error."),
    "neural-foundations": ("An MLP composes affine maps with nonlinear activations to represent nonlinear functions.", r"$h=\phi(Wx+b)$. Stable softmax is $\operatorname{softmax}(z)_i=e^{z_i-m}/\sum_j e^{z_j-m}$ with $m=\max z$."),
    "backpropagation": ("Backpropagation reuses the chain rule from outputs toward inputs.", r"If $z=Wx+b$, then $\partial L/\partial W=(\partial L/\partial z)x^\top$. Cache forward values needed by local derivatives."),
    "pytorch-basics": ("Autograd records tensor operations, while modules organize trainable parameters.", r"The loop is zero gradients, compute $\hat y$, compute $L$, call backward, then update $\theta\leftarrow\theta-\eta\nabla_\theta L$."),
    "essential-layers": ("Initialization and train/eval behavior control signal scale and regularization.", r"Xavier targets $\operatorname{Var}(W_{ij})\approx2/(n_{\rm in}+n_{\rm out})$. Batch norm uses batch statistics during training and running statistics in evaluation."),
    "cnn-theory": ("Convolution exploits locality and weight sharing, giving translation-equivariant feature maps.", r"$y_{oij}=\sum_{cuv}K_{ocuv}x_{c,i+u,j+v}$. Output width is $\lfloor(W+2p-k)/s\rfloor+1$."),
    "cnn-programming": ("A convolution implementation extracts each local window and computes kernel inner products.", r"A layer with $C_{\rm in}$ input channels, $C_{\rm out}$ filters, and $k\times k$ kernels has $C_{\rm out}(C_{\rm in}k^2+1)$ parameters with bias."),
    "round-1-review": ("Review by retrieving definitions and derivations before looking at notes.", r"Connect $X^\top X$ to OLS and PCA, and connect the chain rule to backpropagation. A formula is useful only when its assumptions and shapes are known."),
    "integrated-practice": ("Integrated problems require selecting tools rather than being told which chapter applies.", r"Track dimensions through every derivation: if $X\in\mathbb R^{n\times d}$, then $X^\top X\in\mathbb R^{d\times d}$ and $\nabla_w L\in\mathbb R^d$."),
    "timed-practice-i": ("Timed work rewards triage: secure short definitions, then derivations, then debugging.", r"Budget by points and verify invariants such as $\sum_i\operatorname{softmax}(z)_i=1$ and nonincreasing k-means objective."),
    "timed-practice-ii": ("A mock becomes learning only after errors are classified and repaired.", r"Separate conceptual, algebra, shape, and implementation errors; then solve a parallel problem without notes to test the repair."),
    "final-review": ("Final review compresses knowledge into callable mental templates.", r"Memorize anchors such as $w=X^+y$, $A=U\Sigma V^\top$, and $\theta\leftarrow\theta-\eta\nabla L$, but rehearse deriving them."),
    "attention-mechanisms": ("Attention retrieves a weighted mixture of values using query-key similarity.", r"$\operatorname{Attn}(Q,K,V)=\operatorname{softmax}(QK^\top/\sqrt{d_k})V$. Masks add $-\infty$ to forbidden logits before softmax."),
    "transformer-architecture": ("A transformer alternates token mixing by attention and feature mixing by an MLP.", r"Each sublayer uses a residual $x+\mathcal F(x)$ and normalization. Multi-head outputs are $\operatorname{Concat}(H_1,\dots,H_h)W_O$."),
    "transformer-applications": ("Masking and information flow distinguish encoders, decoders, and encoder-decoder models.", r"Autoregressive models factor $p(x_{1:T})=\prod_t p(x_t\mid x_{<t})$; vision transformers treat projected image patches as tokens."),
    "nlp-tokenize": ("Tokenizers map text to discrete IDs; embeddings map those IDs to vectors.", r"An embedding table $E\in\mathbb R^{V\times d}$ returns row $E_{t_i}$. Subwords balance vocabulary size against sequence length."),
    "nlp-pretraining": ("Pretraining learns reusable representations from broad data; fine-tuning adapts them.", r"Causal language modeling minimizes $-\sum_t\log p_\theta(x_t\mid x_{<t})$. Evaluate on held-out data and match metrics to the task."),
    "object-detection": ("Detection predicts both class confidence and location for multiple objects.", r"$\operatorname{IoU}(A,B)=|A\cap B|/|A\cup B|$. Non-max suppression keeps high scores and removes strongly overlapping duplicates."),
    "unet-segmentation": ("U-Net combines coarse semantic context with high-resolution encoder features.", r"Dice coefficient is $2\sum_i p_i y_i/(\sum_i p_i+\sum_i y_i)$; add smoothing for empty masks."),
    "autoencoders": ("An encoder compresses input to a latent code and a decoder reconstructs it.", r"Train with $L=\|x-g_\theta(f_\phi(x))\|^2$. A bottleneck or corruption prevents a trivial identity map."),
    "variational-autoencoders": ("A VAE learns a distribution over latent codes and a probabilistic decoder.", r"$\mathrm{ELBO}=E_{q(z|x)}[\log p(x|z)]-D_{\rm KL}(q(z|x)\|p(z))$, with $z=\mu+\sigma\odot\epsilon$."),
    "gans": ("A generator creates samples while a discriminator distinguishes generated from real data.", r"$\min_G\max_D E_x\log D(x)+E_z\log(1-D(G(z)))$. Alternating optimization can suffer instability and mode collapse."),
    "diffusion-models": ("Diffusion adds noise gradually, then learns to reverse the corruption.", r"$x_t=\sqrt{\bar\alpha_t}x_0+\sqrt{1-\bar\alpha_t}\epsilon$ and a common objective is $E\|\epsilon-\epsilon_\theta(x_t,t)\|^2$."),
    "stable-diffusion": ("Latent diffusion runs denoising in a compressed VAE space and conditions with text.", r"Classifier-free guidance combines predictions as $\epsilon_{\rm uncond}+s(\epsilon_{\rm cond}-\epsilon_{\rm uncond})$; excessive $s$ reduces diversity."),
    "round-2-review": ("Round 2 unifies sequence mixing, dense vision prediction, and generative modeling.", r"Compare objectives: next-token cross-entropy, Dice overlap, VAE ELBO, GAN minimax loss, and diffusion noise MSE."),
    "round-2-practice-i": ("Practice selecting the correct architecture and loss from the data structure and output.", r"State tensor shapes before coding attention: $QK^\top$ is $T_q\times T_k$, its rows softmax to one, and multiplying $V$ yields $T_q\times d_v$."),
    "round-2-practice-ii": ("Use mixed mocks to expose confusion between superficially similar methods.", r"Ask what is optimized, what is sampled, and what information is available: these distinguish VAEs, GANs, diffusion, causal attention, and bidirectional attention."),
}


def all_lessons() -> list[dict]:
    """Return at least one substantive, available lesson for every topic."""
    lessons = []
    for topic in TOPICS:
        slug = topic["slug"]
        intuition, details = NOTES[slug]
        body = f"""## Intuition

{intuition}

## Definition and core mathematics

{details}

## How to reason about it

Start by naming the input and output shapes, then state the objective or invariant. Work one tiny numerical example before generalizing. Check boundary cases and explain what each term contributes.

## Common mistakes

- Applying a formula without checking its assumptions or dimensions.
- Confusing training-time information with information available at evaluation.
- Trusting code because it runs instead of testing a known small case.
- Memorizing vocabulary without being able to derive or implement the central operation.
"""
        lessons.append({
            "slug": f"{slug}-core",
            "topic": slug,
            "sequence": 1,
            "title": f"{topic['title']}: core ideas",
            "stage": "learn",
            "body_markdown": body,
            "available": True,
        })
    return lessons
