-- Start every level-2 section except the Abstract on a new page (Word output)
local pb = pandoc.RawBlock('openxml', '<w:p><w:r><w:br w:type="page"/></w:r></w:p>')
function Header(el)
  if el.level == 2 and pandoc.utils.stringify(el) ~= 'Abstract' then
    return {pb, el}
  end
end
