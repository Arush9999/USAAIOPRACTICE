"""Browser-runnable project specifications."""


def _project(slug, round_, topic, title, objectives, requirements, math_notes, starter, tests, hints):
    return {
        "slug": slug, "round": round_, "topic": topic, "title": title,
        "objectives": objectives, "requirements": requirements,
        "math_notes": math_notes, "starter_code": starter, "tests_code": tests,
        "rubric": "Correctness 60%; numerical robustness 20%; readable shapes, names, and documentation 20%.",
        "hints": hints,
    }


PROJECTS = [
    _project(
        "numpy-toolkit", 1, "numpy-foundations", "NumPy Array Toolkit",
        "Practice broadcasting, reductions, normalization, and pairwise geometry.",
        "Implement standardize and squared_distances without loops; handle constant columns.",
        r"$z=(x-\mu)/\sigma$ and $\|x-y\|_2^2=\sum_j(x_j-y_j)^2$.",
        "import numpy as np\n\ndef standardize(X):\n    pass\n\ndef squared_distances(X,Y):\n    pass\n",
        "X=np.array([[1.,2.],[3.,2.]])\nZ,mu,s=standardize(X)\nassert np.allclose(Z.mean(0),0)\nassert np.isfinite(Z).all()\nD=squared_distances(X,X)\nassert np.allclose(D,D.T) and np.allclose(np.diag(D),0)",
        ["Broadcast sample and centroid axes.", "Replace zero standard deviations with one."],
    ),
    _project(
        "linear-logistic-regression", 1, "supervised-learning-i", "Linear and Logistic Regression",
        "Connect closed-form regression, gradient descent, sigmoid probabilities, and losses.",
        "Implement linear_fit(X,y), sigmoid(z), and logistic_gradient(X,y,w). Bias columns are supplied.",
        r"$w=X^+y$, $\sigma(z)=1/(1+e^{-z})$, and $\nabla L=X^\top(\sigma(Xw)-y)/n$.",
        "import numpy as np\n\ndef linear_fit(X,y):\n    pass\n\ndef sigmoid(z):\n    pass\n\ndef logistic_gradient(X,y,w):\n    pass\n",
        "X=np.array([[1.,0.],[1.,1.],[1.,2.]])\ny=np.array([1.,3.,5.])\nassert np.allclose(linear_fit(X,y),[1,2])\nassert np.allclose(sigmoid(np.array([0.])),[.5])\ng=logistic_gradient(X,np.array([0.,0.,1.]),np.zeros(2))\nassert g.shape==(2,) and np.isfinite(g).all()",
        ["Use pinv rather than explicitly inverting X.T@X.", "Clip or branch sigmoid for very large magnitudes."],
    ),
    _project(
        "pca-from-scratch", 1, "unsupervised-learning", "PCA from Scratch",
        "Learn centering, SVD, dimensionality reduction, and reconstruction.",
        "Create a PCA class with fit, transform, and inverse_transform; store mean_ and components_.",
        r"For centered $X=U\Sigma V^\top$, the first $k$ rows of $V^\top$ are principal directions.",
        "import numpy as np\n\nclass PCA:\n    def __init__(self,k): self.k=k\n    def fit(self,X):\n        pass\n    def transform(self,X):\n        pass\n    def inverse_transform(self,Z):\n        pass\n",
        "X=np.array([[0.,0.],[1.,0.],[2.,0.]])\np=PCA(1); p.fit(X); Z=p.transform(X); R=p.inverse_transform(Z)\nassert Z.shape==(3,1)\nassert np.allclose(R,X)\nassert np.allclose(np.linalg.norm(p.components_,axis=1),1)",
        ["Center with the training mean.", "Keep Vt[:k]."],
    ),
    _project(
        "k-means-from-scratch", 1, "unsupervised-learning", "K-means from Scratch",
        "Implement Lloyd's assignment/update loop and reason about its objective.",
        "Implement fit_kmeans(X, initial, steps), returning centroids and labels; preserve a centroid if its cluster is empty.",
        r"Each iteration cannot increase $J=\sum_i\|x_i-\mu_{c_i}\|_2^2$ when assignment and means are exact.",
        "import numpy as np\n\ndef fit_kmeans(X, initial, steps=20):\n    pass\n",
        "X=np.array([[0.,0.],[0.,1.],[9.,9.],[10.,9.]])\nC,y=fit_kmeans(X,np.array([[0.,0.],[10.,10.]]))\nassert set(y.tolist())=={0,1}\nassert np.allclose(np.sort(C[:,0]),[0,9.5])",
        ["Compute all sample-centroid distances at once.", "Update each nonempty cluster with its mean."],
    ),
    _project(
        "numpy-mlp", 1, "backpropagation", "Two-layer NumPy MLP",
        "Build a complete forward pass, cross-entropy loss, manual backward pass, and update.",
        "Implement softmax, forward(X,params), and train_step(X,y,params,lr). Use ReLU and integer class labels.",
        r"$H=\operatorname{ReLU}(XW_1+b_1)$, $P=\operatorname{softmax}(HW_2+b_2)$; backpropagate from $(P-Y)/n$.",
        "import numpy as np\n\ndef softmax(z):\n    pass\n\ndef forward(X,p):\n    pass\n\ndef train_step(X,y,p,lr=.1):\n    pass\n",
        "X=np.array([[1.,0.],[0.,1.]])\np={'W1':np.array([[1.,-1.],[-1.,1.]]),'b1':np.zeros(2),'W2':np.eye(2),'b2':np.zeros(2)}\nP=forward(X,p)\nassert P.shape==(2,2) and np.allclose(P.sum(1),1)\nold=p['W2'].copy(); loss=train_step(X,np.array([0,1]),p)\nassert np.isfinite(loss) and not np.allclose(old,p['W2'])",
        ["Cache X, preactivations, hidden activations, and probabilities.", "Subtract row maxima in softmax."],
    ),
    _project(
        "pytorch-mlp", 1, "pytorch-basics", "PyTorch-style MLP Training Loop",
        "Understand module, optimizer, and training-loop responsibilities using a browser-safe NumPy model.",
        "Implement numpy_train_step(X,y,state,lr) with the same zero-gradient/forward/loss/backward/update phases as PyTorch. Include comments mapping phases to PyTorch calls.",
        r"For squared error, $\partial\|XW+b-y\|^2/\partial W=2X^\top(XW+b-y)/n$.",
        "import numpy as np\n\ndef numpy_train_step(X,y,state,lr=.01):\n    # model.train(); optimizer.zero_grad()\n    pass\n",
        "X=np.array([[1.,0.],[0.,1.]])\ny=np.array([[1.],[2.]])\ns={'W':np.zeros((2,1)),'b':np.zeros(1)}\nbefore=((X@s['W']+s['b']-y)**2).mean()\nloss=numpy_train_step(X,y,s,.1)\nafter=((X@s['W']+s['b']-y)**2).mean()\nassert np.isfinite(loss) and after<before",
        ["Compute gradients before mutating state.", "PyTorch's backward populates gradients; optimizer.step mutates parameters."],
    ),
]
