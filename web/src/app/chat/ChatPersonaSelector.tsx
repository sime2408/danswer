import { Persona } from "@/app/admin/assistants/interfaces";
import { FiCheck, FiChevronDown } from "react-icons/fi";
import { CustomDropdown } from "@/components/Dropdown";

function PersonaItem({
  id,
  name,
  onSelect,
  isSelected,
}: {
  id: number;
  name: string;
  onSelect: (personaId: number) => void;
  isSelected: boolean;
}) {
  return (
    <div
      key={id}
      className={`
    flex
    px-3 
    text-sm 
    py-2 
    my-0.5
    rounded
    mx-1
    select-none 
    cursor-pointer 
    text-emphasis dark:text-gray-400
    bg-background dark:bg-neutral-800
    hover:bg-hover dark:hover:bg-neutral-800
  `}
      onClick={() => {
        onSelect(id);
      }}
    >
      {name}
      {isSelected && (
        <div className="ml-auto mr-1">
          <FiCheck />
        </div>
      )}
    </div>
  );
}

export function ChatPersonaSelector({
  personas,
  selectedPersonaId,
  onPersonaChange,
}: {
  personas: Persona[];
  selectedPersonaId: number | null;
  onPersonaChange: (persona: Persona | null) => void;
}) {
  const currentlySelectedPersona = personas.find(
    (persona) => persona.id === selectedPersonaId
  );

  return (
    <CustomDropdown
      dropdown={
        <div
          className={`
            border 
            border-border dark:border-neutral-900 
            bg-background dark:bg-neutral-800
            rounded-lg 
            flex 
            flex-col 
            w-64 
            max-h-96 
            overflow-y-auto 
            flex
            overscroll-contain`}
        >
          {personas.map((persona, ind) => {
            const isSelected = persona.id === selectedPersonaId;
            return (
              <PersonaItem
                key={persona.id}
                id={persona.id}
                name={persona.name}
                onSelect={(clickedPersonaId) => {
                  const clickedPersona = personas.find(
                    (persona) => persona.id === clickedPersonaId
                  );
                  if (clickedPersona) {
                    onPersonaChange(clickedPersona);
                  }
                }}
                isSelected={isSelected}
              />
            );
          })}
        </div>
      }
    >
      <div className="select-none text-xl font-bold flex px-2 py-1.5 text-strong dark:text-strong-dark rounded cursor-pointer hover:bg-neutral-200 dark:hover:bg-neutral-600">
        <div className="my-auto">
          {currentlySelectedPersona?.name || "Default"}
        </div>
        <FiChevronDown className="my-auto ml-1" />
      </div>
    </CustomDropdown>
  );
}
