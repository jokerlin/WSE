(TeX-add-style-hook
 "report"
 (lambda ()
   (TeX-add-to-alist 'LaTeX-provided-class-options
                     '(("elsarticle" "preprint" "review" "12pt")))
   (TeX-run-style-hooks
    "latex2e"
    "elsarticle"
    "elsarticle12"
    "graphicx"
    "caption"
    "subcaption"
    "amssymb")
   (LaTeX-add-labels
    "fig:wiki1")
   (LaTeX-add-environments
    "ruullee")
   (LaTeX-add-bibliographies
    "sample"))
 :latex)

