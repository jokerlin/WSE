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
    "amssymb")
   (LaTeX-add-bibliographies
    "sample"))
 :latex)

